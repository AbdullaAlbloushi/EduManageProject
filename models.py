from datetime import datetime
from app import db
import sqlalchemy.orm as so
import sqlalchemy as sa
from typing import List, Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Student(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    major: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    studentnumber: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    gpa: so.Mapped[float] = so.mapped_column(sa.Float)
    grades: so.Mapped[List["GradeSheet"]] = so.relationship(back_populates="student")
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), nullable=True)
    reminder_days: so.Mapped[int] = so.mapped_column(sa.Integer, default=1)


class Teacher(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(256), index=True)
    major: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    TeacherNumber: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    Teacheremail: so.Mapped[str] = so.mapped_column(sa.String(255), nullable=False)
    courses: so.Mapped[List["Course"]] = so.relationship(back_populates="teacher")
    user_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("user.id"), nullable=True)


class Course(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    classname: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    teacher_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Teacher.id))
    teacher: so.Mapped[Teacher] = so.relationship(back_populates="courses")
    grades: so.Mapped[List["GradeSheet"]] = so.relationship(back_populates="course")


class GradeSheet(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    student_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Student.id))
    course_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Course.id))
    student: so.Mapped[Student] = so.relationship(back_populates="grades")
    course: so.Mapped[Course] = so.relationship(back_populates="grades")


class activities(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    activity_name: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)


class User(db.Model, UserMixin):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    role: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    deadline: so.Mapped[datetime] = so.mapped_column(sa.DateTime, index=True)
    feedback_deadline: so.Mapped[datetime] = so.mapped_column(sa.DateTime, index=True)

    course_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("course.id"))

    ec_requests: so.Mapped[List["ECRequest"]] = so.relationship(back_populates="task")
    submissions: so.Mapped[List["TaskSubmission"]] = so.relationship(back_populates="task")


class ECRequest(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    student_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("student.id"))
    task_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("task.id"))

    reason: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    status: so.Mapped[str] = so.mapped_column(sa.String(30), default="pending")

    evidence_link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    evidence_filename: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    extension_days: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)

    # Additional information workflow
    additional_info_required: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    wellbeing_message: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    additional_evidence_filename: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    additional_evidence_link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(500))
    additional_info_submitted_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)

    task: so.Mapped["Task"] = so.relationship(back_populates="ec_requests")
    student: so.Mapped["Student"] = so.relationship()


class TaskSubmission(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    task_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("task.id"), nullable=False)
    student_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("student.id"), nullable=False)

    individual_deadline: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)
    individual_feedback_deadline: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False)

    extension_days: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    submitted: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    submission_time: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime, nullable=True)

    feedback_given: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    feedback_time: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime, nullable=True)
    feedback_content: so.Mapped[Optional[str]] = so.mapped_column(sa.Text, nullable=True)

    task: so.Mapped["Task"] = so.relationship(back_populates="submissions")
    student: so.Mapped["Student"] = so.relationship()


class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), nullable=False)
    sender_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("user.id"), nullable=True)

    type: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)
    message: so.Mapped[str] = so.mapped_column(sa.String(500), nullable=False)

    task_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("task.id"), nullable=True)
    ec_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("ec_request.id"), nullable=True)

    is_read: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, default=datetime.utcnow)

    recipient: so.Mapped["User"] = so.relationship(foreign_keys=[recipient_id])
    sender: so.Mapped[Optional["User"]] = so.relationship(foreign_keys=[sender_id])
    task: so.Mapped[Optional["Task"]] = so.relationship()
    ec: so.Mapped[Optional["ECRequest"]] = so.relationship()


from app import login


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))