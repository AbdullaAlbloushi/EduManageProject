from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    SubmitField,
    SelectField,
    FloatField,
    IntegerField,
    PasswordField,
    BooleanField,
    TextAreaField
)
from wtforms.validators import DataRequired, Email, NumberRange
from wtforms.fields import DateTimeLocalField


class StudentForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    major = StringField("Major", validators=[DataRequired()])
    studentnumber = IntegerField("Student ID", validators=[DataRequired()])
    gpa = FloatField("GPA", validators=[DataRequired()])
    submit = SubmitField("Add Student")


class TeacherForm(FlaskForm):
    name = StringField("Teacher Name", validators=[DataRequired()])
    major = StringField("Faculty / Department", validators=[DataRequired()])
    teacher_number = IntegerField("Staff ID", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Add Teacher")


class CourseForm(FlaskForm):
    classname = StringField("Course Name", validators=[DataRequired()])
    teacher_id = IntegerField("Teacher ID", validators=[DataRequired()])
    submit = SubmitField("Create Course")


class activityForm(FlaskForm):
    activityname = StringField("Activity Name", validators=[DataRequired()])


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ECSubmissionForm(FlaskForm):
    task_id = SelectField('Select Task', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason for Extension', validators=[DataRequired()], render_kw={"rows": 5})
    evidence_link = StringField('Evidence Link (Optional)')
    evidence_file = FileField(
        'Upload Evidence File (Optional)',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only JPG, PNG, PDF allowed')]
    )
    submit = SubmitField('Submit EC Application')


class ECEditForm(FlaskForm):
    extension_days = IntegerField(
        "Extension Days",
        validators=[DataRequired(), NumberRange(min=0, max=365)]
    )

    submit = SubmitField("Save Changes")


class DeadlineEditForm(FlaskForm):
    deadline = DateTimeLocalField(
        "New Deadline",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()]
    )

    submit = SubmitField("Update Deadline")


class ReminderSettingsForm(FlaskForm):
    reminder_days = SelectField(
        "Reminder Time",
        choices=[
            (1, "1 day before"),
            (3, "3 days before"),
            (7, "7 days before"),
            (14, "14 days before")
        ],
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Settings")