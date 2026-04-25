from app import app, db
from app.models import User, Teacher, Student, Course, Task, TaskSubmission
from datetime import datetime, timedelta


with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database tables recreated.")

    admin = User(username="admin", role="admin")
    admin.set_password("admin123")

    wellbeing = User(username="wellbeing1", role="wellbeing")
    wellbeing.set_password("wellbeing123")

    teacher_user = User(username="teacher1", role="teacher")
    teacher_user.set_password("teacher123")

    student_user = User(username="student1", role="student")
    student_user.set_password("student123")

    db.session.add_all([admin, wellbeing, teacher_user, student_user])
    db.session.flush()
    print("User accounts created.")

    teacher = Teacher(
        name="Dr Abdulla",
        major="School of Computer Science",
        TeacherNumber=10001,
        Teacheremail="abdulla@university.ac.uk",
        user_id=teacher_user.id
    )
    db.session.add(teacher)
    db.session.flush()
    print("Teacher record created.")

    course = Course(
        classname="Python Programming",
        teacher_id=teacher.id
    )
    db.session.add(course)
    db.session.flush()
    print("Course created.")

    student = Student(
        name="Daniel Ahmed",
        major="Computer Science",
        studentnumber=20240001,
        gpa=3.5,
        user_id=student_user.id,
        reminder_days=3
    )
    db.session.add(student)
    db.session.flush()
    print("Student record created.")

    task1_deadline = datetime.now() + timedelta(days=7)
    task2_deadline = datetime.now() + timedelta(days=14)

    task1 = Task(
        title="Assignment 1: Python Basics",
        description="Complete the basic Python practice exercises.",
        deadline=task1_deadline,
        feedback_deadline=task1_deadline + timedelta(days=7),
        course_id=course.id
    )

    task2 = Task(
        title="Midterm Project: Data Analysis Report",
        description="Use pandas to analyse a dataset and write a short report.",
        deadline=task2_deadline,
        feedback_deadline=task2_deadline + timedelta(days=7),
        course_id=course.id
    )

    db.session.add_all([task1, task2])
    db.session.flush()
    print("Tasks created.")

    submission1 = TaskSubmission(
        task_id=task1.id,
        student_id=student.id,
        individual_deadline=task1.deadline,
        individual_feedback_deadline=task1.feedback_deadline,
        extension_days=0,
        submitted=False,
        feedback_given=False
    )

    submission2 = TaskSubmission(
        task_id=task2.id,
        student_id=student.id,
        individual_deadline=task2.deadline,
        individual_feedback_deadline=task2.feedback_deadline,
        extension_days=0,
        submitted=False,
        feedback_given=False
    )

    db.session.add_all([submission1, submission2])
    db.session.commit()
    print("Task submission records created.")

    print("\n" + "=" * 50)
    print("Database initialisation complete.")
    print("=" * 50)
    print("Role          Username       Password")
    print("Admin         admin          admin123")
    print("Wellbeing     wellbeing1     wellbeing123")
    print("Teacher       teacher1       teacher123")
    print("Student       student1       student123")
    print("=" * 50)
    print("\nSuggested demo flow:")
    print("1. Log in as student1 and submit an EC request.")
    print("2. Log in as wellbeing1 and review/approve/request more information.")
    print("3. Log in as admin and record extension days.")
    print("4. Log in as teacher1 and check notifications/task overview.")
    print("=" * 50)