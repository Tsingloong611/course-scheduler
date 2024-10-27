from flask import Flask, render_template, request, render_template_string

app = Flask(__name__)

# 定义早八时间段
early_slots = {"一1-2", "二1-2", "三1-2", "四1-2", "五1-2"}


def is_early(time):
    return time in early_slots


def has_time_conflict(selected_times, time_slots):
    return any(time in selected_times for time in time_slots)


def select_optimal_courses(course_options):
    min_early_classes = len(course_options)
    best_schedule = []
    solution_found = False  # 用于检测是否找到有效解

    def recurse(course_index, current_schedule, selected_times, early_class_count):
        nonlocal min_early_classes, best_schedule, solution_found
        if course_index == len(course_options):
            solution_found = True  # 表示找到至少一个可行解
            if early_class_count < min_early_classes:
                min_early_classes = early_class_count
                best_schedule = list(current_schedule)
            return

        course = course_options[course_index]

        for option in course["options"]:
            if has_time_conflict(selected_times, option["timeSlots"]):
                continue

            contains_early = any(is_early(time) for time in option["timeSlots"])
            current_schedule.append({
                "courseName": course["name"],
                "section": option["section"],
                "timeSlots": option["timeSlots"]
            })
            selected_times.update(option["timeSlots"])
            recurse(
                course_index + 1,
                current_schedule,
                selected_times,
                early_class_count + (1 if contains_early else 0)
            )
            selected_times.difference_update(option["timeSlots"])
            current_schedule.pop()

    recurse(0, [], set(), 0)
    return best_schedule, min_early_classes, solution_found


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        course_data = request.form.get("courses").strip().split("\n")

        course_options = []
        for course in course_data:
            course_info = course.strip().split(",")
            if len(course_info) < 3:
                return render_template_string(
                    '<p style="color: red;">请检查输入格式，每行应为：课程名称,班级,时间段1&时间段2...</p>')

            course_name = course_info[0].strip()
            section = course_info[1].strip()
            time_slots = course_info[2].strip().split("&")

            existing_course = next((c for c in course_options if c["name"] == course_name), None)
            if existing_course:
                existing_course["options"].append({"section": section, "timeSlots": time_slots})
            else:
                course_options.append({
                    "name": course_name,
                    "options": [{"section": section, "timeSlots": time_slots}]
                })

        best_schedule, min_early_classes, solution_found = select_optimal_courses(course_options)

        if not solution_found:
            return render_template_string(
                '<p style="color: red;">无法找到满足所有课程的排课方案，请调整课程时间或班级设置。</p>'
            )

        return render_template_string(
            '''
            <h2>优化后的课程安排</h2>
            <ul>
                {% for course in best_schedule %}
                    <li>课程名称: {{ course.courseName }}, 班级: {{ course.section }}, 时间段: {{ course.timeSlots | join(", ") }}</li>
                {% endfor %}
            </ul>
            <p>最少的早八课程数: {{ min_early_classes }}</p>
            ''', best_schedule=best_schedule, min_early_classes=min_early_classes
        )

    return render_template("index.html", best_schedule=None)


if __name__ == "__main__":
    app.run(debug=True)
