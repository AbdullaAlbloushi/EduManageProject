# Testing Checklist

## Testing Objectives
Verify that the notification system, role permissions, and reminder features are functioning correctly across all user accounts.

---

## Testing Steps

### Test 1: Student Submits EC Application
- [ ] Login as a student.
- [ ] Navigate to the "My Schedule" page.
- [ ] Click the option to submit an EC Request.
- [ ] Fill in a reason and attach an evidence file.
- [ ] Submit the application.
- [ ] **Expected Result:** The system displays a success message confirming the application was submitted.

### Test 2: Admin Views EC and Sends Reminder
- [ ] Login as an admin.
- [ ] Navigate to the "EC Overview" page.
- [ ] **Verify:** The newly submitted EC application is visible.
- [ ] **Verify:** The statistics show one pending application.
- [ ] **Verify:** There are no buttons to approve or reject the application (read-only access).
- [ ] Locate the pending application and click the button to remind the Wellbeing department.
- [ ] **Expected Result:** The system displays a success message confirming the reminder was sent.

### Test 3: Wellbeing Receives Reminder and Processes
- [ ] Login as a wellbeing staff member.
- [ ] **Verify:** The notification icon in the sidebar shows an unread badge.
- [ ] Open the notification center.
- [ ] **Verify:** The reminder from the admin is visible, displaying the correct student name and task title.
- [ ] Click the link in the notification to view the pending requests.
- [ ] Locate the application, set the extension days (e.g., 5 days), and approve it.
- [ ] **Expected Result:** The system displays a success message confirming the approval and the updated extension days.

### Test 4: Teacher Receives Automatic Notification
- [ ] Login as a teacher.
- [ ] **Verify:** The notification icon in the sidebar shows an unread badge.
- [ ] Open the notification center.
- [ ] **Verify:** The notification confirming the EC approval and the automatic feedback deadline extension is visible.
- [ ] Mark the notification as read.
- [ ] **Expected Result:** The unread styling and the sidebar badge disappear.

### Test 5: Teacher Views Extension Status
- [ ] Keep the teacher account logged in.
- [ ] Navigate to the "Task Overview" page.
- [ ] **Verify:** The student's status badge clearly shows the application was extended.
- [ ] **Verify:** The student's individual submission deadline is shifted by the correct number of days.
- [ ] **Verify:** The teacher's feedback deadline for that student is also shifted by the exact same number of days.

### Test 6: Mark All Notifications as Read
- [ ] Login to any account with unread notifications.
- [ ] Navigate to the notification center.
- [ ] Click the option to mark all notifications as read.
- [ ] **Expected Result:** All unread styling is removed and the page indicates there are no new notifications.

### Test 7: Admin Permission Verification
- [ ] Login as an admin.
- [ ] **Verify:** The sidebar does not contain a link to the main Wellbeing EC management page.
- [ ] Attempt to manually type the Wellbeing management URL into the browser.
- [ ] **Expected Result:** The system blocks access and redirects the user with a permission error message.

### Test 8: Cross-Role Notification System Test
- [ ] Login to all four role types sequentially (Student, Teacher, Wellbeing, Admin).
- [ ] **Verify:** Every role has access to the communication and notification center.
- [ ] **Verify:** Users can only see notifications explicitly sent to their own accounts.

### Test 9: Student Checks EC Status
- [ ] Login as a student.
- [ ] Navigate to the "My Schedule" page.
- [ ] Scroll to "My EC Status".
- [ ] **Verify:** The submitted EC application is visible.
- [ ] **Verify:** The status is shown as pending, approved, or rejected.
- [ ] **Verify:** The evidence file or evidence link is visible.
- [ ] **Expected Result:** The student can track the EC application status clearly.

### Test 10: Wellbeing Requests Additional Evidence and Student Responds
- [ ] Login as a wellbeing staff member.
- [ ] Navigate to "Pending Requests".
- [ ] Click "Request More Info" for a pending EC application.
- [ ] Enter a message requesting additional evidence.
- [ ] Submit the request.
- [ ] Login as the student.
- [ ] Navigate to "My Schedule".
- [ ] **Verify:** The EC request is highlighted as requiring additional information.
- [ ] Click "Submit Additional Info".
- [ ] Upload an additional file or provide a link.
- [ ] Submit.
- [ ] **Expected Result:** The additional evidence is submitted and visible to Wellbeing.

### Test 11: Teacher Gives Feedback
- [ ] Login as a teacher.
- [ ] Navigate to "Task Overview".
- [ ] Click "Give Feedback" for a student submission.
- [ ] Enter feedback text.
- [ ] Submit the feedback.
- [ ] **Expected Result:** The feedback is saved and the student receives a notification.
---

## Acceptance Criteria

1. Students can successfully submit EC applications.
2. Admins can view all applications but cannot approve or reject them.
3. Admins can successfully send reminders to the Wellbeing team.
4. The Wellbeing team receives reminder notifications correctly.
5. The Wellbeing team can approve or reject applications.
6. Teachers are automatically notified when an application for their course is approved.
7. Both student submission deadlines and teacher feedback deadlines are automatically extended upon approval.
8. Unread notification badges display accurate counts.