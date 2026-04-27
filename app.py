from flask import Flask, render_template, request, session, redirect
from Config import config
from Database.db_conn import get_conn

app = Flask(__name__)
app.config.from_object(config())
app.secret_key = "your_secret_key"

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')
# ===================== LOGIN =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[3]

            if user[3] == 'admin':
                return redirect('/admin')
            elif user[3] == 'manager':
                return redirect('/manager')
            elif user[3] == 'teacher':
                return redirect('/teacher')
            elif user[3] == 'student':
                return redirect('/student')

        return "Invalid Credentials"

    return render_template('login.html')


# ===================== ADD FORMS =====================
@app.route('/add_student_form')
def add_student_form():
    return render_template('add_student.html')

@app.route('/add_teacher_form')
def add_teacher_form():
    return render_template('add_teacher.html')

@app.route('/add_manager_form')
def add_manager_form():
    return render_template('add_manager.html')


# ===================== ADMIN =====================
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return "Access Denied"

    conn = get_conn()
    cur = conn.cursor()

    # 👨‍🎓 Students
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

    # 👨‍🏫 Teachers
    cur.execute("SELECT * FROM teachers")
    teachers = cur.fetchall()

    # 📚 Courses (WITH department name)
    cur.execute("""
        SELECT courses.course_id,
               courses.name,
               departments.name
        FROM courses
        JOIN departments ON courses.department_id = departments.department_id
    """)
    courses = cur.fetchall()

    # 🏢 Departments
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()

    # 🔗 Enrollments (JOIN → student + course names)
    cur.execute("""
        SELECT enrollments.enrollment_id,
               students.name,
               courses.name
        FROM enrollments
        JOIN students ON enrollments.student_id = students.student_id
        JOIN courses ON enrollments.course_id = courses.course_id
    """)
    enrollments = cur.fetchall()

    # 🔗 Teacher-Course mapping (JOIN → teacher + course names)
    cur.execute("""
        SELECT teacher_courses.id,
               teachers.name,
               courses.name
        FROM teacher_courses
        JOIN teachers ON teacher_courses.teacher_id = teachers.teacher_id
        JOIN courses ON teacher_courses.course_id = courses.course_id
    """)
    teacher_courses = cur.fetchall()

    # 👥 Managers
    cur.execute("SELECT * FROM users WHERE role='manager'")
    managers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        students=students,
        teachers=teachers,
        courses=courses,
        departments=departments,
        enrollments=enrollments,
        teacher_courses=teacher_courses,
        managers=managers
    )

# ===================== MANAGER =====================
@app.route('/manager')
def manager():
    if session.get('role') not in ['manager', 'admin']:
        return "Access Denied"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

    cur.execute("SELECT * FROM teachers")
    teachers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('manager_dashboard.html',
                           students=students,
                           teachers=teachers)


# ===================== TEACHER =====================
@app.route('/teacher')
def teacher():
    if session.get('role') not in ['teacher', 'admin']:
        return "Access Denied"

    conn = get_conn()
    cur = conn.cursor()

    # 🔑 FIX: get real teacher_id
    cur.execute("""
        SELECT teacher_id 
        FROM teachers 
        WHERE user_id = %s
    """, (session.get('user_id'),))

    result = cur.fetchone()

    if not result:
        return "Teacher not found"

    teacher_id = result[0]

    # 📚 My Courses
    cur.execute("""
        SELECT courses.course_id,
               courses.name,
               departments.name
        FROM teacher_courses
        JOIN courses ON teacher_courses.course_id = courses.course_id
        JOIN departments ON courses.department_id = departments.department_id
        WHERE teacher_courses.teacher_id = %s
    """, (teacher_id,))
    courses = cur.fetchall()

    # 👨‍🎓 Students in my courses
    cur.execute("""
        SELECT students.student_id,
               students.name,
               courses.name
        FROM enrollments
        JOIN students ON enrollments.student_id = students.student_id
        JOIN courses ON enrollments.course_id = courses.course_id
        JOIN teacher_courses ON teacher_courses.course_id = courses.course_id
        WHERE teacher_courses.teacher_id = %s
    """, (teacher_id,))
    students = cur.fetchall()

    # 📊 Marks
    cur.execute("""
        SELECT marks.mark_id,
               students.name,
               courses.name,
               marks.exam_type,
               marks.marks_obtained,
               marks.total_marks
        FROM marks
        JOIN students ON marks.student_id = students.student_id
        JOIN courses ON marks.course_id = courses.course_id
        JOIN teacher_courses ON teacher_courses.course_id = courses.course_id
        WHERE teacher_courses.teacher_id = %s
    """, (teacher_id,))
    marks = cur.fetchall()

    # 🧾 Attendance
    cur.execute("""
        SELECT attendance.attendance_id,
               students.name,
               courses.name,
               attendance.attendance_date,
               attendance.status
        FROM attendance
        JOIN students ON attendance.student_id = students.student_id
        JOIN courses ON attendance.course_id = courses.course_id
        JOIN teacher_courses ON teacher_courses.course_id = courses.course_id
        WHERE teacher_courses.teacher_id = %s
    """, (teacher_id,))
    attendance = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'teacher_dashboard.html',
        courses=courses,
        students=students,
        marks=marks,
        attendance=attendance
    )
# ===================== STUDENT =====================
@app.route('/student')
def student():
    if session.get('role') != 'student':
        return "Access Denied"

    user_id = session.get('user_id')

    conn = get_conn()
    cur = conn.cursor()

    # 👨‍🎓 Get student profile
    cur.execute("""
        SELECT student_id, name, father_name, contact, gender
        FROM students
        WHERE user_id = %s
    """, (user_id,))
    student = cur.fetchone()

    if not student:
        return "Student not found"

    student_id = student[0]

    # 📚 My Courses
    cur.execute("""
        SELECT courses.course_id,
               courses.name
        FROM enrollments
        JOIN courses ON enrollments.course_id = courses.course_id
        WHERE enrollments.student_id = %s
    """, (student_id,))
    courses = cur.fetchall()

    # 📊 My Marks
    cur.execute("""
        SELECT courses.name,
               marks.exam_type,
               marks.marks_obtained,
               marks.total_marks
        FROM marks
        JOIN courses ON marks.course_id = courses.course_id
        WHERE marks.student_id = %s
    """, (student_id,))
    marks = cur.fetchall()

    # 🧾 My Attendance
    cur.execute("""
        SELECT courses.name,
               attendance.attendance_date,
               attendance.status
        FROM attendance
        JOIN courses ON attendance.course_id = courses.course_id
        WHERE attendance.student_id = %s
    """, (student_id,))
    attendance = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'student_dashboard.html',
        student=student,
        courses=courses,
        marks=marks,
        attendance=attendance
    )

# ===================== ADD USERS =====================
@app.route('/add', methods=['GET', 'POST'])
def add():
    role = session.get('role')

    if role not in ['admin', 'manager']:
        return "Access Denied"

    if request.method == 'POST':

        user_type = request.form.get('user_type')

        conn = get_conn()
        cur = conn.cursor()

        if user_type == 'student':

            cur.execute("""
                INSERT INTO users (email, password, role)
                VALUES (%s, %s, 'student')
                RETURNING user_id
            """, (request.form['email'], request.form['password']))

            user_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO students (user_id, name, father_name, age, date_of_birth, contact, gender)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id,
                request.form['name'],
                request.form['father_name'],
                request.form['age'],
                request.form['date_of_birth'],
                request.form['contact'],
                request.form['gender']
            ))

        elif user_type == 'teacher':

            cur.execute("""
                INSERT INTO users (email, password, role)
                VALUES (%s, %s, 'teacher')
                RETURNING user_id
            """, (request.form['email'], request.form['password']))

            user_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO teachers (user_id, name, father_name, age, date_of_birth, contact, gender, education)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id,
                request.form['name'],
                request.form['father_name'],
                request.form['age'],
                request.form['date_of_birth'],
                request.form['contact'],
                request.form['gender'],
                request.form['education']
            ))

        elif user_type == 'manager' and role == 'admin':

            cur.execute("""
                INSERT INTO users (email, password, role)
                VALUES (%s, %s, 'manager')
            """, (
                request.form['email'],
                request.form['password']
            ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect('/admin')

    return render_template('add.html')


# ===================== COURSE =====================
@app.route('/add_course', methods=['GET','POST'])
def add_course():
    if session.get("role") not in ['manager','admin']:
        return "Access Denied"

    if request.method == "POST":
        name = request.form['name']
        department_id = request.form['department_id']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO courses(name, department_id) VALUES(%s,%s)",
            (name, department_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        return "Course Added"

    return render_template('add_course.html')


# ===================== UPDATE COURSE FIX =====================
@app.route('/update_course', methods=['GET','POST'])
def update_course():
    if session.get("role") not in ['manager','admin']:
        return "Access Denied"

    if request.method == "POST":
        name = request.form['name']
        department_id = request.form['department_id']
        course_id = request.form['course_id']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            UPDATE courses 
            SET name=%s, department_id=%s 
            WHERE course_id=%s
        """, (name, department_id, course_id))

        conn.commit()
        cur.close()
        conn.close()

        return "Course Updated"

    return render_template('update_course.html')


# ===================== DEPARTMENT =====================
@app.route("/add_department", methods=['GET','POST'])
def add_department():
    if session.get("role") not in ['manager','admin']:
        return "Access Denied"

    if request.method == "POST":
        name = request.form['name']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("INSERT INTO departments(name) VALUES(%s)", (name,))

        conn.commit()
        cur.close()
        conn.close()

        return "Department Added"

    return render_template('add_Deptartment.html')


# ===================== ENROLLMENT =====================
@app.route("/add_enrollment", methods=['GET','POST'])
def add_enrollment():
    if session.get("role") not in ['manager','admin']:
        return "Access Denied"

    if request.method == "POST":
        student_id = request.form['student_id']
        course_id = request.form['course_id']

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO enrollments(student_id, course_id)
            VALUES(%s,%s)
        """, (student_id, course_id))

        conn.commit()
        cur.close()
        conn.close()

        return "Enrollment Added"

    return render_template('add_enrollment.html')


# ===================== TEACHER COURSES FIX =====================
@app.route('/teacher_courses')
def teacher_courses():
    if session.get("role") != "teacher":
        return "Access Denied"

    user_id = session.get("user_id")

    conn = get_conn()
    cur = conn.cursor()

    # FIX: get teacher_id from user_id
    cur.execute("SELECT teacher_id FROM teachers WHERE user_id=%s", (user_id,))
    teacher = cur.fetchone()

    if not teacher:
        return "Teacher not found"

    teacher_id = teacher[0]

    cur.execute("""
        SELECT c.course_id, c.name
        FROM courses c
        JOIN teacher_courses tc ON c.course_id = tc.course_id
        WHERE tc.teacher_id = %s
    """, (teacher_id,))

    courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('teacher_courses.html', courses=courses)


# ===================== ADD MARKS (FIXED + CLEAN) =====================
@app.route('/add_marks', methods=['GET', 'POST'])
def add_marks():
    if session.get("role") != "teacher":
        return "Access Denied"

    teacher_id = session.get("user_id")

    if request.method == "POST":
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        exam_type = request.form['exam_type']
        marks_obtained = request.form['marks_obtained']
        total_marks = request.form['total_marks']

        conn = get_conn()
        cur = conn.cursor()

        # 🔐 SECURITY: check teacher-course assignment
        cur.execute("""
            SELECT 1 FROM teacher_courses
            WHERE teacher_id=%s AND course_id=%s
        """, (teacher_id, course_id))

        if not cur.fetchone():
            cur.close()
            conn.close()
            return "Not allowed for this course"

        # ✅ INSERT CORRECT TABLE STRUCTURE
        cur.execute("""
            INSERT INTO marks (student_id, course_id, exam_type, marks_obtained, total_marks)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, course_id, exam_type, marks_obtained, total_marks))

        conn.commit()
        cur.close()
        conn.close()

        return "Marks Added Successfully ✅"

    return render_template("add_marks.html")



# ===================== ADD ATTENDANCE (FIXED) =====================
@app.route('/add_attendance', methods=['GET', 'POST'])
def add_attendance():
    if session.get("role") != "teacher":
        return "Access Denied"

    teacher_id = session.get("user_id")

    if request.method == "POST":
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        attendance_date = request.form['attendance_date']
        status = request.form['status']

        conn = get_conn()
        cur = conn.cursor()

        # 🔐 SECURITY CHECK
        cur.execute("""
            SELECT 1 FROM teacher_courses
            WHERE teacher_id=%s AND course_id=%s
        """, (teacher_id, course_id))

        if not cur.fetchone():
            cur.close()
            conn.close()
            return "Not allowed"

        cur.execute("""
            INSERT INTO attendance (student_id, course_id, attendance_date, status)
            VALUES (%s, %s, %s, %s)
        """, (student_id, course_id, attendance_date, status))

        conn.commit()
        cur.close()
        conn.close()

        return "Attendance Marked ✅"

    return render_template("add_attendance.html")


# ===================== assign_teacher_course =====================
@app.route('/assign_teacher_course', methods=['POST'])
def assign_teacher_course():
    if session.get('role') != 'admin':
        return "Access Denied"

    teacher_id = request.form['teacher_id']
    course_id = request.form['course_id']

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO teacher_courses (teacher_id, course_id)
        VALUES (%s, %s)
    """, (teacher_id, course_id))

    conn.commit()
    cur.close()
    conn.close()

    return "Teacher assigned successfully"
# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True, port=5001)