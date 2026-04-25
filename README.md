# EduManage: Student EC & Deadline Management System

## Project Overview
EduManage is a role-based web application built to streamline the Extenuating Circumstances (EC) application process within a university setting. It bridges the communication gap between Students, Teachers, the Wellbeing Department, and System Administrators by providing a centralized platform for managing assignment deadlines, extension requests, and evidence submissions.

## Key Features

### 1. Role-Based Access Control
The system features strict separation of duties across four dedicated user roles:
* **Students:** Can view their schedules, submit EC applications, upload evidence, and provide supplementary materials if requested.
* **Wellbeing Department:** Reviews EC applications, requests additional information, and holds exclusive rights to approve or reject extensions.
* **Teachers:** Gain a clear overview of student progress and receive automated updates regarding deadline shifts.
* **System Administrators:** Manage global student data, system deadlines, and can manually override extension days in special cases.

### 2. Universal Notification System
A cross-role communication hub keeps all users informed without relying on external email chains.
* **Automated Alerts:** Teachers are automatically notified when a student's EC is approved.
* **Manual Reminders:** Admins can ping the Wellbeing department regarding pending applications.
* **Real-time Badges:** Users see unread notification counts upon logging in.

### 3. Automated Deadline Synchronization
When the Wellbeing department approves an EC request, the system automatically recalculates both the student's submission deadline and the teacher's grading/feedback deadline, ensuring scheduling consistency across the application.

### 4. Asynchronous UI Interactions
The interface utilizes JavaScript and the Fetch API to provide seamless, in-page modal interactions (e.g., editing extension days or requesting additional info) without requiring full page reloads.

## Tech Stack
* **Backend:** Python 3, Flask
* **Database:** SQLite, SQLAlchemy (ORM)
* **Authentication:** Flask-Login, Werkzeug Security
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Jinja2 Templating
* **Forms:** Flask-WTF

## Setup & Installation

1. **Install Dependencies:**
   Ensure you have Python installed, then install the required packages:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

2. **Initialize the Database:**
   Run the initialization script to build the SQLite database and populate the test accounts:
   \`\`\`bash
   python init_db.py
   \`\`\`

3. **Run the Application:**
   Start the local Flask development server:
   \`\`\`bash
   python run.py
   \`\`\`
   The application will be accessible at `http://127.0.0.1:5000`.

## Test Accounts
Use the following credentials to explore the different role perspectives:

| Role | Username | Password |
|------|----------|----------|
| System Admin | admin | admin123 |
| Wellbeing Staff | wellbeing1 | wellbeing123 |
| Teacher | teacher1 | teacher123 |
| Student | student1 | student123 |