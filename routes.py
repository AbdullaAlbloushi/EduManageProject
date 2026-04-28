import os
import uuid
from flask import render_template, redirect, url_for, flash, request, send_from_directory, abort, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from app import app, db
from app.models import Student, Teacher, Course, GradeSheet, activities, Notification
from app.forms import StudentForm, TeacherForm, CourseForm, activityForm, LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User

# Upload file storage directory (uploads folder in project root)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

# Ensure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_storage):
    """Save uploaded file, return unique filename. Returns None if failed."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_FOLDER, unique_name))
    return unique_name


def notify_teacher_of_task(task, ntype, message, ec=None):
    course = db.session.get(Course, task.course_id)
    if not course:
        return
    teacher = db.session.get(Teacher, course.teacher_id)
    if not teacher or not teacher.user_id:
        return
    notif = Notification(
        recipient_id=teacher.user_id,
        sender_id=current_user.id if current_user.is_authenticated else None,
        type=ntype,
        message=message,
        task_id=task.id,
        ec_id=ec.id if ec else None,
    )
    db.session.add(notif)


# ─────────────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    actform = activityForm()
    if actform.validate_on_submit():
        act = activities(activity_name=actform.activityname.data)
        db.session.add(act)
        db.session.commit()
        return redirect(url_for('index'))
    acts = activities.query.all()
    return render_template('index.html', form=actform, acts=acts)


@app.route('/studentpage', methods=['GET', 'POST'])
@login_required
def studentpage():
    # Only admin can access
    if current_user.role != 'admin':
        flash("Only Admin can access this page")
        return redirect(url_for('index'))

    sform = StudentForm()
    if sform.validate_on_submit():
        # Auto-create user account
        # Username format: s + student number (e.g. s12345678)
        username = f"s{sform.studentnumber.data}"

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f"Username {username} already exists, cannot create duplicate account")
            return redirect(url_for('studentpage'))

        # Create new user
        new_user = User(
            username=username,
            role='student'
        )
        # Default password: password123 (can be modified as needed)
        new_user.set_password('password123')
        db.session.add(new_user)
        db.session.flush()  # Immediately get user.id

        # Create student record and associate with new user
        student = Student(
            name=sform.name.data,
            major=sform.major.data,
            studentnumber=sform.studentnumber.data,
            gpa=sform.gpa.data,
            user_id=new_user.id
        )
        db.session.add(student)
        db.session.flush()  # Immediately get student.id

        # Create TaskSubmission records for all existing tasks for this new student
        all_tasks = Task.query.all()
        for task in all_tasks:
            submission = TaskSubmission(
                task_id=task.id,
                student_id=student.id,
                individual_deadline=task.deadline,
                individual_feedback_deadline=task.feedback_deadline,
                extension_days=0,
                submitted=False,
                feedback_given=False
            )
            db.session.add(submission)

        db.session.commit()

        flash(f"Student {student.name} added! Username: {username}, Default password: password123")
        return redirect(url_for('studentpage'))
    students = Student.query.all()
    return render_template('studentpage.html', form=sform, students=students)


@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    """Delete a student and their associated user account"""
    if current_user.role != 'admin':
        flash("Only Admin can delete students")
        return redirect(url_for('index'))

    student = db.session.get(Student, student_id)
    if not student:
        flash("Student not found")
        return redirect(url_for('studentpage'))

    student_name = student.name
    user_id = student.user_id

    # Delete associated TaskSubmissions
    TaskSubmission.query.filter_by(student_id=student_id).delete()

    # Delete associated EC requests
    ECRequest.query.filter_by(student_id=student_id).delete()

    # Delete associated GradeSheets
    GradeSheet.query.filter_by(student_id=student_id).delete()

    # Delete student record
    db.session.delete(student)

    # Delete associated user account
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            # Delete notifications sent by or to this user
            Notification.query.filter(
                (Notification.sender_id == user_id) | (Notification.recipient_id == user_id)
            ).delete()
            db.session.delete(user)

    db.session.commit()
    flash(f"Student {student_name} and associated account have been deleted successfully")
    return redirect(url_for('studentpage'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


from app.models import Task, ECRequest, TaskSubmission
from app.forms import ECSubmissionForm, ECEditForm, DeadlineEditForm, ReminderSettingsForm
from datetime import datetime, timedelta


@app.route('/my_tasks', methods=['GET', 'POST'])
@login_required
def my_tasks():
    if current_user.role != 'student':
        flash("Only students can access this page")
        return redirect(url_for('index'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student record not found, please contact admin.")
        return redirect(url_for('index'))

    all_tasks = Task.query.all()
    form = ECSubmissionForm()
    form.task_id.choices = [(t.id, t.title) for t in all_tasks]

    if form.validate_on_submit():
        # Check if EC already submitted for this task
        existing_ec = ECRequest.query.filter_by(
            student_id=student.id,
            task_id=form.task_id.data
        ).first()

        if existing_ec:
            flash("You have already submitted an EC application for this task")
            return redirect(url_for('my_tasks'))

        # Handle file upload
        filename = save_uploaded_file(form.evidence_file.data)

        new_ec = ECRequest(
            student_id=student.id,
            task_id=form.task_id.data,
            reason=form.reason.data,
            evidence_link=form.evidence_link.data or None,
            evidence_filename=filename,
            status='pending'
        )
        db.session.add(new_ec)
        db.session.flush()  # Immediately get EC ID

        # Notify all Wellbeing users
        task = db.session.get(Task, form.task_id.data)
        wellbeing_users = User.query.filter_by(role='wellbeing').all()
        for wellbeing_user in wellbeing_users:
            notification = Notification(
                recipient_id=wellbeing_user.id,
                sender_id=current_user.id,
                type='ec_submitted',
                message=(
                    f"📝 New EC Application\n\n"
                    f"Student {student.name} submitted a new EC application\n"
                    f"Task: {task.title}\n"
                    f"Please review in Pending Requests page."
                ),
                ec_id=new_ec.id
            )
            db.session.add(notification)

        db.session.commit()
        flash("EC application submitted, pending Wellbeing review.")
        return redirect(url_for('my_tasks'))

    my_ecs = ECRequest.query.filter_by(student_id=student.id).all()

    # Calculate reminder status for each task
    now = datetime.now()
    reminder_days = student.reminder_days if student.reminder_days else 1
    tasks_with_reminder = []
    for task in all_tasks:
        time_until_deadline = task.deadline - now
        should_remind = time_until_deadline.total_seconds() > 0 and time_until_deadline.days <= reminder_days
        tasks_with_reminder.append({
            'task': task,
            'should_remind': should_remind,
            'days_left': time_until_deadline.days if time_until_deadline.total_seconds() > 0 else -1
        })

    return render_template('my_tasks.html', tasks=tasks_with_reminder, form=form,
                         my_ecs=my_ecs, reminder_days=reminder_days)


# View evidence files (images display directly, PDF download)
@app.route('/evidence/view/<int:ec_id>')
@login_required
def view_evidence(ec_id):
    # Only admin, wellbeing, and file owner (student) can view
    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        abort(404)

    is_owner = (current_user.role == 'student' and
                ec.student.user_id == current_user.id)
    is_staff = current_user.role in ('admin', 'wellbeing')

    if not is_owner and not is_staff:
        abort(403)

    # Determine which file type to view
    file_type = request.args.get('type', 'original')
    if file_type == 'additional':
        filename = ec.additional_evidence_filename
    else:
        filename = ec.evidence_filename

    if not filename:
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/evidence/download/<int:ec_id>')
@login_required
def download_evidence(ec_id):
    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        abort(404)

    is_staff = current_user.role in ('admin', 'wellbeing')
    if not is_staff:
        abort(403)


    file_type = request.args.get('type', 'original')
    if file_type == 'additional':
        filename = ec.additional_evidence_filename
        prefix = "Supplement"
    else:
        filename = ec.evidence_filename
        prefix = "Original"

    if not filename:
        abort(404)

    ext = filename.rsplit('.', 1)[1]
    download_name = secure_filename(f"{prefix}_{ec.student.name}_{ec.task.title}.{ext}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename,
                               as_attachment=True, download_name=download_name)


@app.route('/wellbeing/manage')
@login_required
def wellbeing_manage():
    if current_user.role != 'wellbeing':
        flash("Only Wellbeing department can access this page")
        return redirect(url_for('index'))
    all_ecs = ECRequest.query.all()
    return render_template('wellbeing_manage.html', ecs=all_ecs)


@app.route('/wellbeing/approve/<int:ec_id>/<string:action>')
@login_required
def approve_ec(ec_id, action):
    if current_user.role != 'wellbeing':
        flash("Only Wellbeing department can approve/reject EC applications")
        return redirect(url_for('index'))

    ec = db.session.get(ECRequest, ec_id)
    if ec:
        if action == 'approve':
            ec.status = 'approved'

            # Automatically adjust student's task deadline and feedback deadline
            submission = TaskSubmission.query.filter_by(
                task_id=ec.task_id,
                student_id=ec.student_id
            ).first()

            if submission:
                # Update extension days
                submission.extension_days = ec.extension_days
                # Extend student's submission deadline
                submission.individual_deadline = ec.task.deadline + timedelta(days=ec.extension_days)
                # Synchronously extend teacher's feedback deadline
                submission.individual_feedback_deadline = ec.task.feedback_deadline + timedelta(days=ec.extension_days)

            # Notify student: EC application approved
            student_user = db.session.get(User, ec.student.user_id)
            if student_user:
                notification = Notification(
                    recipient_id=student_user.id,
                    sender_id=current_user.id,
                    type='ec_approved',
                    message=(
                        f"✅ EC Application Approved\n\n"
                        f"Your EC application for '{ec.task.title}' has been approved!\n"
                        f"Extension: {ec.extension_days} day(s)"
                    ),
                    ec_id=ec.id
                )
                db.session.add(notification)

            # Notify all Admin: Wellbeing approved, need to set extension days
            admin_users = User.query.filter_by(role='admin').all()
            for admin_user in admin_users:
                notification = Notification(
                    recipient_id=admin_user.id,
                    sender_id=current_user.id,
                    type='ec_approved_need_admin_action',
                    message=(
                        f"⏰ EC Approved, Please Set Extension Days\n\n"
                        f"Wellbeing approved {ec.student.name}'s EC application for '{ec.task.title}'\n"
                        f"Current extension: {ec.extension_days} day(s)\n"
                        f"Please review in EC & Deadlines page."
                    ),
                    ec_id=ec.id
                )
                db.session.add(notification)

            flash(f"Application approved for {ec.student.name}, deadline extended by {ec.extension_days} day(s)")
            notify_teacher_of_task(
                ec.task, ntype='ec_approved',
                message=(
                    f"Student {ec.student.name}'s EC application for '{ec.task.title}' has been approved, "
                    f"with an extension of {ec.extension_days} day(s). Your feedback deadline is also extended."
                ), ec=ec
            )
        elif action == 'reject':
            ec.status = 'rejected'

            # Notify student: EC application rejected
            student_user = db.session.get(User, ec.student.user_id)
            if student_user:
                notification = Notification(
                    recipient_id=student_user.id,
                    sender_id=current_user.id,
                    type='ec_rejected',
                    message=(
                        f"❌ EC Application Rejected\n\n"
                        f"Sorry, your EC application for '{ec.task.title}' has been rejected."
                    ),
                    ec_id=ec.id
                )
                db.session.add(notification)

            flash(f"Application by {ec.student.name} has been rejected")
            notify_teacher_of_task(
                ec.task, ntype='ec_rejected',
                message=(
                    f"Student {ec.student.name}'s EC application for '{ec.task.title}' has been rejected."
                ), ec=ec
            )
        db.session.commit()
    return redirect(url_for('wellbeing_manage'))


@app.route('/wellbeing/request_additional_info/<int:ec_id>', methods=['POST'])
@login_required
def request_additional_info(ec_id):
    """Wellbeing requests additional materials from student"""
    if current_user.role != 'wellbeing':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Only Wellbeing can perform this action'}), 403
        flash("Only Wellbeing can perform this action")
        return redirect(url_for('index'))

    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'EC application not found'}), 404
        flash("EC application not found")
        return redirect(url_for('wellbeing_manage'))

    # Get message content
    if request.is_json:
        message = request.json.get('message')
    else:
        message = request.form.get('message')

    if not message or not message.strip():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Message is required'}), 400
        flash("Message is required")
        return redirect(url_for('wellbeing_manage'))

    # Update EC record
    ec.additional_info_required = True
    ec.wellbeing_message = message.strip()

    # Send notification to student
    student_user = db.session.get(User, ec.student.user_id)
    if student_user:
        notification = Notification(
            recipient_id=student_user.id,
            sender_id=current_user.id,
            type='additional_info_required',
            message=(
                f"📎 Additional Information Required\n\n"
                f"Task: {ec.task.title}\n"
                f"Message: {message}\n\n"
                f"Please go to My Schedule page to view and submit additional materials."
            ),
            ec_id=ec.id
        )
        db.session.add(notification)

    db.session.commit()

    # AJAX response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'Additional info request sent to {ec.student.name}'
        })

    flash(f"Additional info request sent to {ec.student.name}")
    return redirect(url_for('wellbeing_manage'))


@app.route('/student/submit_additional_info/<int:ec_id>', methods=['POST'])
@login_required
def submit_additional_info(ec_id):
    """Student submits additional materials"""
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Only students can perform this action'}), 403

    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        return jsonify({'success': False, 'message': 'EC application not found'}), 404

    # Verify this is the student's application
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student or ec.student_id != student.id:
        return jsonify({'success': False, 'message': 'Unauthorized to access this application'}), 403

    # Verify if additional materials are required
    if not ec.additional_info_required:
        return jsonify({'success': False, 'message': 'Additional info not required for this application'}), 400

    # Verify if already submitted
    if ec.additional_info_submitted_at:
        return jsonify({'success': False, 'message': 'Additional info already submitted'}), 400

    # Handle file upload
    additional_file = request.files.get('additional_file')
    additional_link = request.form.get('additional_link')

    if not additional_file and not additional_link:
        return jsonify({'success': False, 'message': 'Please upload a file or provide a link'}), 400

    # Save file
    if additional_file and additional_file.filename:
        filename = save_uploaded_file(additional_file)
        if filename:
            ec.additional_evidence_filename = filename
        else:
            return jsonify({'success': False, 'message': 'File upload failed, please check file format'}), 400

    # Save link
    if additional_link:
        ec.additional_evidence_link = additional_link

    # Update submission time
    from datetime import datetime
    ec.additional_info_submitted_at = datetime.utcnow()
    # Note: Keep additional_info_required = True, use additional_info_submitted_at to determine if submitted

    # Send notification to Wellbeing
    wellbeing_users = User.query.filter_by(role='wellbeing').all()
    for wellbeing_user in wellbeing_users:
        notification = Notification(
            recipient_id=wellbeing_user.id,
            sender_id=current_user.id,
            type='additional_info_submitted',
            message=(
                f"📎 Additional Info Submitted\n\n"
                f"Student {student.name} submitted additional materials\n"
                f"Task: {ec.task.title}\n"
                f"Please review in Pending Requests page."
            ),
            ec_id=ec.id
        )
        db.session.add(notification)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Additional info submitted successfully, Wellbeing will review soon'
    })


@app.route('/admin/ec/edit/<int:ec_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_ec(ec_id):
    # Only Admin can access this page
    if current_user.role != 'admin':
        flash("Admin access only")
        return redirect(url_for('index'))

    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        flash("Application not found")
        return redirect(url_for('admin_ec_overview'))

    form = ECEditForm(obj=ec)

    if form.validate_on_submit():
        # Admin is not allowed to modify EC status.
        # If the EC has already been rejected by Wellbeing,
        # Admin is also not allowed to modify extension days.
        if ec.status == 'rejected':
            flash("This EC application was rejected by Wellbeing. Admin cannot modify extension days.")
            return redirect(url_for('admin_ec_overview'))

        # Only allow Admin to modify extension_days
        ec.extension_days = form.extension_days.data

        # If the EC is approved, update the student's individual deadline
        # and the teacher's feedback deadline.
        if ec.status == 'approved':
            submission = TaskSubmission.query.filter_by(
                task_id=ec.task_id,
                student_id=ec.student_id
            ).first()

            if submission:
                submission.extension_days = ec.extension_days
                submission.individual_deadline = ec.task.deadline + timedelta(days=ec.extension_days)
                submission.individual_feedback_deadline = ec.task.feedback_deadline + timedelta(days=ec.extension_days)

        # Notify teacher about the extension update
        notify_teacher_of_task(
            ec.task,
            ntype='ec_updated',
            message=(
                f"Admin updated {ec.student.name}'s EC application for '{ec.task.title}': "
                f"extension changed to {ec.extension_days} day(s). "
                f"Status remains {ec.status}."
            ),
            ec=ec
        )

        db.session.commit()
        flash(
            f"Updated {ec.student.name}'s EC application "
            f"(extension: {ec.extension_days} day(s), status: {ec.status})"
        )

        # Redirect Admin back to the Admin EC overview, not the Wellbeing page
        return redirect(url_for('admin_ec_overview'))

    return render_template('admin_edit_ec.html', form=form, ec=ec)

@app.route('/admin/ec_overview')
@login_required
def admin_ec_overview():
    """Admin views all EC applications (read-only, can remind wellbeing)"""
    if current_user.role != 'admin':
        flash("Admin access only")
        return redirect(url_for('index'))
    all_ecs = ECRequest.query.order_by(ECRequest.created_at.desc()).all()
    return render_template('admin_ec_overview.html', ecs=all_ecs)


@app.route('/admin/ec/edit_extension/<int:ec_id>', methods=['POST'])
@login_required
def admin_edit_extension(ec_id):
    """Admin edits EC application extension days via AJAX"""
    if current_user.role != 'admin':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Admin access only'}), 403
        flash("Admin access only")
        return redirect(url_for('index'))

    ec = db.session.get(ECRequest, ec_id)
    if not ec:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        flash("Application not found")
        return redirect(url_for('admin_ec_overview'))

    # New: rejected EC cannot be edited by admin
    if ec.status == 'rejected':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'This EC application was rejected by Wellbeing. Admin cannot modify extension days.'
            }), 403
        flash("This EC application was rejected by Wellbeing. Admin cannot modify extension days.")
        return redirect(url_for('admin_ec_overview'))

    # Get extension days
    if request.is_json:
        extension_days = request.json.get('extension_days')
    else:
        extension_days = request.form.get('extension_days')

    # Validate extension days
    try:
        extension_days = int(extension_days)
        if extension_days < 0 or extension_days > 365:
            raise ValueError("Extension days must be between 0-365")
    except (TypeError, ValueError) as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'Invalid extension days: {str(e)}'}), 400
        flash(f"Invalid extension days: {str(e)}")
        return redirect(url_for('admin_ec_overview'))

    # Update extension days
    old_extension_days = ec.extension_days
    ec.extension_days = extension_days

    # If EC approved, synchronously update student's deadline
    if ec.status == 'approved':
        submission = TaskSubmission.query.filter_by(
            task_id=ec.task_id,
            student_id=ec.student_id
        ).first()

        if submission:
            # Update student's submission deadline and feedback deadline
            submission.extension_days = extension_days
            submission.individual_deadline = ec.task.deadline + timedelta(days=extension_days)
            submission.individual_feedback_deadline = ec.task.feedback_deadline + timedelta(days=extension_days)

    # Notify teacher: Student received extension, remind teacher to update feedback time
    notify_teacher_of_task(
        ec.task, ntype='ec_extension_set',
        message=(
            f"📅 Student Extension Approved\n\n"
            f"Student {ec.student.name} received {extension_days} day(s) extension for '{ec.task.title}'.\n"
            f"Original extension: {old_extension_days} days\n"
            f"New extension: {extension_days} days\n\n"
            f"Your feedback deadline has been automatically extended. Click the link below to view task details."
        ), ec=ec
    )

    db.session.commit()

    # AJAX response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'Extension days updated to {extension_days} day(s) for {ec.student.name}'
        })

    flash(f"Extension days updated to {extension_days} day(s) for {ec.student.name}")
    return redirect(url_for('admin_ec_overview'))


@app.route('/admin/tasks', methods=['GET'])
@login_required
def admin_tasks():
    if current_user.role != 'admin':
        flash("Admin access only")
        return redirect(url_for('index'))
    tasks = Task.query.order_by(Task.deadline).all()
    return render_template('admin_tasks.html', tasks=tasks)


@app.route('/admin/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_deadline(task_id):
    if current_user.role != 'admin':
        # AJAX request returns JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Admin access only'}), 403
        flash("Admin access only")
        return redirect(url_for('index'))

    task = db.session.get(Task, task_id)
    if not task:
        # AJAX request returns JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        flash("Task not found")
        return redirect(url_for('admin_tasks'))

    if request.method == 'POST':
        # Handle form submission (supports AJAX and traditional forms)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            deadline_str = request.form.get('deadline') or request.json.get('deadline')
            if not deadline_str:
                return jsonify({'success': False, 'message': 'Deadline is required'}), 400

            try:
                from datetime import datetime
                new_deadline_dt = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                old_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')
                task.deadline = new_deadline_dt
                new_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')

                notify_teacher_of_task(
                    task, ntype='deadline_changed',
                    message=(
                        f"The deadline for '{task.title}' has been updated from {old_deadline} to {new_deadline}."
                    )
                )
                db.session.commit()

                return jsonify({
                    'success': True,
                    'message': f"Deadline for '{task.title}' updated to {new_deadline}",
                    'new_deadline': new_deadline
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Update failed: {str(e)}'}), 500
        else:
            # Traditional form submission
            form = DeadlineEditForm(obj=task)
            if form.validate_on_submit():
                old_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')
                task.deadline = form.deadline.data
                new_deadline = task.deadline.strftime('%Y-%m-%d %H:%M')
                notify_teacher_of_task(
                    task, ntype='deadline_changed',
                    message=(
                        f"The deadline for '{task.title}' has been updated from {old_deadline} to {new_deadline}."
                    )
                )
                db.session.commit()
                flash(
                    f"Deadline for '{task.title}' updated to {new_deadline}"
                )
                return redirect(url_for('admin_tasks'))

    # GET request - display form
    form = DeadlineEditForm(obj=task)
    if request.method == 'GET':
        form.deadline.data = task.deadline
    return render_template('admin_edit_deadline.html', form=form, task=task)


# Universal notification system (all roles)
@app.route('/notifications')
@login_required
def notifications():
    """Notification center for all roles"""
    notifications = (
        Notification.query
        .filter_by(recipient_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template('notifications.html', notifications=notifications)


@app.route('/notifications/read/<int:notif_id>')
@login_required
def mark_notification_read_universal(notif_id):
    """Mark notification as read (universal)"""
    notif = db.session.get(Notification, notif_id)
    if notif and notif.recipient_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(url_for('notifications'))


@app.route('/notifications/read_all')
@login_required
def mark_all_notifications_read_universal():
    """Mark all notifications as read (universal)"""
    Notification.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.")
    return redirect(url_for('notifications'))


@app.route('/send_reminder/<string:target_role>/<int:related_id>')
@login_required
def send_reminder(target_role, related_id):
    """Send reminder to specified role

    Args:
        target_role: Target role (wellbeing/admin/teacher)
        related_id: Related record ID (EC ID or Task ID)
    """
    # Get context information
    context = request.args.get('context', 'general')  # ec_approval, task_review, etc

    # Find recipients by target role
    target_users = User.query.filter_by(role=target_role).all()

    if not target_users:
        flash(f"No {target_role} users found")
        return redirect(request.referrer or url_for('index'))

    # Generate message based on context
    if context == 'ec_approval':
        ec = db.session.get(ECRequest, related_id)
        if ec:
            # Check if reminder already sent (same sender for same EC)
            existing_reminder = Notification.query.filter_by(
                sender_id=current_user.id,
                type='reminder_ec',
                ec_id=related_id
            ).first()

            if existing_reminder:
                flash("You have already sent a reminder, please do not send again")
                return redirect(request.referrer or url_for('index'))

            message = (
                f"⏰ Reminder: {current_user.username} reminds you to process {ec.student.name}'s EC application for '{ec.task.title}'."
            )
            notif_type = 'reminder_ec'
        else:
            flash("EC application not found")
            return redirect(request.referrer or url_for('index'))
    else:
        message = f"⏰ {current_user.username} sent you a reminder"
        notif_type = 'reminder_general'

    # Send notification to all target role users
    for user in target_users:
        notif = Notification(
            recipient_id=user.id,
            sender_id=current_user.id,
            type=notif_type,
            message=message,
            ec_id=related_id if context == 'ec_approval' else None
        )
        db.session.add(notif)

    db.session.commit()

    flash(
        f"Reminder sent to {target_role} department ({len(target_users)} user(s))"
    )
    return redirect(request.referrer or url_for('index'))


# Teacher-specific notifications (backward compatibility)
@app.route('/teacher/notifications')
@login_required
def teacher_notifications():
    """Teacher notification page (backward compatibility)"""
    if current_user.role != 'teacher':
        flash("Teacher access only")
        return redirect(url_for('index'))
    return redirect(url_for('notifications'))


@app.route('/teacher/notifications/read/<int:notif_id>')
@login_required
def mark_notification_read(notif_id):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.recipient_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(url_for('teacher_notifications'))


@app.route('/teacher/notifications/read_all')
@login_required
def mark_all_notifications_read():
    if current_user.role != 'teacher':
        return redirect(url_for('index'))
    Notification.query.filter_by(
        recipient_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.")
    return redirect(url_for('teacher_notifications'))


@app.context_processor
def inject_unread_notification_count():
    """Inject unread notification count (all roles)"""
    count = 0
    if current_user.is_authenticated:
        count = Notification.query.filter_by(
            recipient_id=current_user.id, is_read=False
        ).count()
    return dict(unread_notification_count=count)


@app.route('/student/reminder_settings', methods=['GET', 'POST'])
@login_required
def reminder_settings():
    if current_user.role != 'student':
        flash("Only students can access this page")
        return redirect(url_for('index'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash("Student record not found, please contact admin.")
        return redirect(url_for('index'))

    form = ReminderSettingsForm()

    if form.validate_on_submit():
        student.reminder_days = form.reminder_days.data
        db.session.commit()
        flash(f"Reminder settings updated to {student.reminder_days} day(s) before")
        return redirect(url_for('my_tasks'))

    if request.method == 'GET':
        form.reminder_days.data = student.reminder_days

    return render_template('reminder_settings.html', form=form, student=student)


# Teacher views student submission status and feedback management
@app.route('/teacher/task_overview')
@login_required
def teacher_task_overview():
    """Teacher views all tasks and student submission status"""
    if current_user.role != 'teacher':
        flash("Teacher access only")
        return redirect(url_for('index'))

    # Get teacher information
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash("Teacher record not found")
        return redirect(url_for('index'))

    # Get all courses for this teacher
    courses = Course.query.filter_by(teacher_id=teacher.id).all()
    course_ids = [c.id for c in courses]

    # Get all tasks for these courses
    tasks = Task.query.filter(Task.course_id.in_(course_ids)).order_by(Task.deadline).all()

    # For each task, get all student submission statuses
    task_data = []
    for task in tasks:
        submissions = TaskSubmission.query.filter_by(task_id=task.id).all()
        task_data.append({
            'task': task,
            'submissions': submissions
        })

    return render_template('teacher_task_overview.html', task_data=task_data, teacher=teacher)


@app.route('/teacher/give_feedback/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def give_feedback(submission_id):
    """Teacher provides feedback on student submission"""
    if current_user.role != 'teacher':
        flash("Teacher access only")
        return redirect(url_for('index'))

    submission = db.session.get(TaskSubmission, submission_id)
    if not submission:
        flash("Submission not found")
        return redirect(url_for('teacher_task_overview'))

    if request.method == 'POST':
        feedback_content = request.form.get('feedback_content')
        if feedback_content:
            submission.feedback_content = feedback_content
            submission.feedback_given = True
            submission.feedback_time = datetime.now()

            # Notify student
            student_user = db.session.get(User, submission.student.user_id)
            if student_user:
                notification = Notification(
                    recipient_id=student_user.id,
                    sender_id=current_user.id,
                    type='feedback_given',
                    message=(
                        f"📝 New Feedback Received\n\n"
                        f"Your teacher has provided feedback for '{submission.task.title}'.\n"
                        f"Please log in to view the feedback."
                    ),
                    task_id=submission.task_id
                )
                db.session.add(notification)

            db.session.commit()
            flash(f"Feedback submitted successfully for {submission.student.name}")
        return redirect(url_for('teacher_task_overview'))

    return render_template('give_feedback.html', submission=submission)