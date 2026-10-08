from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


# =========================================================
# USER
# =========================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    # -----------------------------------------------------
    # ROLES
    # -----------------------------------------------------

    ROLE_STUDENT = "student"
    ROLE_PARTNER = "partner"
    ROLE_ADVISER = "adviser"
    ROLE_ADMIN = "admin"

    # -----------------------------------------------------
    # ACCOUNT APPROVAL STATUS
    # -----------------------------------------------------

    APPROVAL_PENDING = "Pending"
    APPROVAL_APPROVED = "Approved"
    APPROVAL_REJECTED = "Rejected"

    # -----------------------------------------------------
    # VERIFICATION DOCUMENT TYPES
    # -----------------------------------------------------

    VERIFICATION_STUDENT_ID = "Student ID"
    VERIFICATION_BUSINESS_PERMIT = "Business Permit"
    VERIFICATION_EMPLOYMENT_PROOF = "Employment/Appointment Proof"

    # -----------------------------------------------------
    # BASIC INFORMATION
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        db.String(80),
        nullable=False
    )

    middle_name = db.Column(
        db.String(80)
    )

    last_name = db.Column(
        db.String(80),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    contact_number = db.Column(
        db.String(20)
    )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # -----------------------------------------------------
    # ROLE
    # -----------------------------------------------------

    role = db.Column(
        db.String(20),
        nullable=False,
        default=ROLE_STUDENT
    )

    # -----------------------------------------------------
    # ACCOUNT APPROVAL
    # -----------------------------------------------------

    approval_status = db.Column(
        db.String(20),
        nullable=False,
        default=APPROVAL_PENDING
    )

    is_active_account = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # -----------------------------------------------------
    # VERIFICATION DOCUMENT
    # -----------------------------------------------------

    verification_document_path = db.Column(
        db.String(255),
        nullable=True
    )

    verification_document_type = db.Column(
        db.String(50),
        nullable=True
    )

    # -----------------------------------------------------
    # CREATED DATE
    # -----------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------------------
    # STUDENT PROFILE
    # -----------------------------------------------------

    student_profile = db.relationship(
        "StudentProfile",
        foreign_keys="StudentProfile.user_id",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # -----------------------------------------------------
    # ADVISER'S ASSIGNED STUDENTS
    # -----------------------------------------------------

    assigned_students = db.relationship(
        "StudentProfile",
        foreign_keys="StudentProfile.adviser_id",
        backref="adviser",
        lazy="dynamic"
    )

    # -----------------------------------------------------
    # INDUSTRY PARTNER PROFILE
    # -----------------------------------------------------

    partner_profile = db.relationship(
        "IndustryPartner",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # -----------------------------------------------------
    # PASSWORD FUNCTIONS
    # -----------------------------------------------------

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(
            self.password_hash,
            raw_password
        )

    # -----------------------------------------------------
    # FULL NAME
    # -----------------------------------------------------

    @property
    def full_name(self):
        parts = [
            self.first_name,
            self.middle_name,
            self.last_name
        ]

        return " ".join(
            p for p in parts if p
        )

    # -----------------------------------------------------
    # APPROVAL HELPERS
    # -----------------------------------------------------

    @property
    def is_approved(self):
        return self.approval_status == self.APPROVAL_APPROVED

    @property
    def is_pending(self):
        return self.approval_status == self.APPROVAL_PENDING

    @property
    def is_rejected(self):
        return self.approval_status == self.APPROVAL_REJECTED

    # -----------------------------------------------------
    # VERIFICATION HELPER
    # -----------------------------------------------------

    @property
    def has_verification_document(self):
        return bool(self.verification_document_path)

    # -----------------------------------------------------
    # APPROVE ACCOUNT
    # -----------------------------------------------------

    def approve_account(self):
        self.approval_status = self.APPROVAL_APPROVED
        self.is_active_account = True

    # -----------------------------------------------------
    # REJECT ACCOUNT
    # -----------------------------------------------------

    def reject_account(self):
        self.approval_status = self.APPROVAL_REJECTED
        self.is_active_account = False

    # -----------------------------------------------------
    # REPRESENTATION
    # -----------------------------------------------------

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# =========================================================
# STUDENT PROFILE
# =========================================================

class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # USER ACCOUNT
    # -----------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # OJT ADVISER
    # -----------------------------------------------------

    adviser_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    # -----------------------------------------------------
    # STUDENT INFORMATION
    # -----------------------------------------------------

    student_id_number = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    course = db.Column(
        db.String(120),
        nullable=False
    )

    year_level = db.Column(
        db.String(20),
        nullable=False
    )

    section = db.Column(
        db.String(20)
    )

    school_year = db.Column(
        db.String(20)
    )

    address = db.Column(
        db.String(255)
    )

    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    skills = db.Column(
        db.String(500)
    )

    preferred_industries = db.Column(
        db.String(500)
    )

    # -----------------------------------------------------
    # STUDENT DOCUMENTS
    # -----------------------------------------------------

    resume_path = db.Column(
        db.String(255)
    )

    application_letter_path = db.Column(
        db.String(255)
    )

    medical_certificate_path = db.Column(
        db.String(255)
    )

    # -----------------------------------------------------
    # INTERNSHIPS
    # -----------------------------------------------------

    internships = db.relationship(
        "Internship",
        backref="student",
        lazy="dynamic"
    )

    # -----------------------------------------------------
    # INTERNSHIP APPLICATIONS
    # -----------------------------------------------------

    internship_applications = db.relationship(
        "InternshipApplication",
        backref="student",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # -----------------------------------------------------
    # SKILLS LIST
    # -----------------------------------------------------

    @property
    def skills_list(self):
        return [
            s.strip()
            for s in (self.skills or "").split(",")
            if s.strip()
        ]

    # -----------------------------------------------------
    # PREFERRED INDUSTRIES LIST
    # -----------------------------------------------------

    @property
    def preferred_industries_list(self):
        return [
            s.strip()
            for s in (self.preferred_industries or "").split(",")
            if s.strip()
        ]


# =========================================================
# INDUSTRY PARTNER
# =========================================================

class IndustryPartner(db.Model):
    __tablename__ = "industry_partners"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # USER ACCOUNT
    # -----------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # COMPANY INFORMATION
    # -----------------------------------------------------

    company_name = db.Column(
        db.String(150),
        nullable=False
    )

    industry = db.Column(
        db.String(120)
    )

    address = db.Column(
        db.String(255)
    )

    available_slots = db.Column(
        db.Integer,
        default=0
    )

    status = db.Column(
        db.String(20),
        default="Active"
    )

    # -----------------------------------------------------
    # INTERNSHIPS
    # -----------------------------------------------------

    internships = db.relationship(
        "Internship",
        backref="company",
        lazy="dynamic"
    )

    # -----------------------------------------------------
    # INTERNSHIP APPLICATIONS
    # -----------------------------------------------------

    internship_applications = db.relationship(
        "InternshipApplication",
        backref="company",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )


# =========================================================
# INTERNSHIP APPLICATION
# =========================================================

class InternshipApplication(db.Model):
    __tablename__ = "internship_applications"

    # -----------------------------------------------------
    # APPLICATION STATUS
    # -----------------------------------------------------

    STATUS_PENDING = "Pending"
    STATUS_ACCEPTED = "Accepted"
    STATUS_REJECTED = "Rejected"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # INDUSTRY PARTNER
    # -----------------------------------------------------

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("industry_partners.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # APPLICATION STATUS
    # -----------------------------------------------------

    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_PENDING
    )

    # -----------------------------------------------------
    # APPLICATION MESSAGE
    # -----------------------------------------------------

    message = db.Column(
        db.Text,
        nullable=True
    )

    # -----------------------------------------------------
    # DATES
    # -----------------------------------------------------

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # -----------------------------------------------------
    # REPRESENTATION
    # -----------------------------------------------------

    def __repr__(self):
        return (
            f"<InternshipApplication "
            f"{self.id} - {self.status}>"
        )


# =========================================================
# INTERNSHIP
# =========================================================

class Internship(db.Model):
    """
    Represents an actual OJT placement.

    An Internship is created after an internship
    application has been accepted.
    """

    __tablename__ = "internships"

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    STATUS_ACTIVE = "Active"
    STATUS_ON_HOLD = "On Hold"
    STATUS_COMPLETED = "Completed"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # COMPANY
    # -----------------------------------------------------

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("industry_partners.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # INTERNSHIP INFORMATION
    # -----------------------------------------------------

    department = db.Column(
        db.String(120)
    )

    supervisor_name = db.Column(
        db.String(120)
    )

    start_date = db.Column(
        db.Date
    )

    end_date = db.Column(
        db.Date
    )

    required_hours = db.Column(
        db.Integer,
        default=240
    )

    completed_hours = db.Column(
        db.Integer,
        default=0
    )

    status = db.Column(
        db.String(20),
        default=STATUS_ACTIVE
    )

    # -----------------------------------------------------
    # WEEKLY REPORTS
    # -----------------------------------------------------

    weekly_reports = db.relationship(
        "WeeklyReport",
        backref="internship",
        lazy="dynamic"
    )

    # -----------------------------------------------------
    # NARRATIVE REPORTS
    # -----------------------------------------------------

    narrative_reports = db.relationship(
        "NarrativeReport",
        backref="internship",
        lazy="dynamic"
    )

    # -----------------------------------------------------
    # EVALUATIONS
    # -----------------------------------------------------

    evaluations = db.relationship(
        "Evaluation",
        backref="internship",
        lazy="dynamic"
    )

    # -----------------------------------------------------
    # CERTIFICATE
    # -----------------------------------------------------

    certificate = db.relationship(
        "Certificate",
        backref="internship",
        uselist=False
    )

    # -----------------------------------------------------
    # ATTENDANCE
    # -----------------------------------------------------

    attendances = db.relationship(
        "Attendance",
        backref="internship",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # -----------------------------------------------------
    # PROGRESS
    # -----------------------------------------------------

    @property
    def progress_percent(self):

        if not self.required_hours:
            return 0

        completed = self.completed_hours or 0
        required = self.required_hours or 0

        return min(
            100,
            round(
                (
                    completed /
                    required
                ) * 100
            )
        )

    # -----------------------------------------------------
    # REMAINING HOURS
    # -----------------------------------------------------

    @property
    def remaining_hours(self):

        required = self.required_hours or 0
        completed = self.completed_hours or 0

        return max(
            0,
            required - completed
        )


# =========================================================
# ATTENDANCE
# =========================================================

class Attendance(db.Model):
    """
    Stores the student's daily OJT attendance.

    One attendance record represents one work session.
    Time In starts the session and Time Out ends it.
    """

    __tablename__ = "attendances"

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    STATUS_PRESENT = "Present"
    STATUS_COMPLETED = "Completed"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # INTERNSHIP
    # -----------------------------------------------------

    internship_id = db.Column(
        db.Integer,
        db.ForeignKey("internships.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # ATTENDANCE DATE
    # -----------------------------------------------------

    attendance_date = db.Column(
        db.Date,
        nullable=False
    )

    # -----------------------------------------------------
    # TIME IN
    # -----------------------------------------------------

    time_in = db.Column(
        db.DateTime,
        nullable=False
    )

    # -----------------------------------------------------
    # TIME OUT
    # -----------------------------------------------------

    time_out = db.Column(
        db.DateTime,
        nullable=True
    )

    # -----------------------------------------------------
    # HOURS RENDERED
    # -----------------------------------------------------

    hours_rendered = db.Column(
        db.Numeric(6, 2),
        default=0
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = db.Column(
        db.String(20),
        default=STATUS_PRESENT
    )

    # -----------------------------------------------------
    # CREATED DATE
    # -----------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------------------
    # CALCULATE HOURS
    # -----------------------------------------------------

    def calculate_hours(self):

        if not self.time_in or not self.time_out:
            return 0

        seconds = (
            self.time_out -
            self.time_in
        ).total_seconds()

        hours = seconds / 3600

        return round(
            max(hours, 0),
            2
        )


# =========================================================
# WEEKLY REPORT
# =========================================================

class WeeklyReport(db.Model):
    __tablename__ = "weekly_reports"

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    STATUS_DRAFT = "Draft"
    STATUS_SUBMITTED = "Submitted"
    STATUS_APPROVED = "Approved"
    STATUS_PENDING = "Pending"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # INTERNSHIP
    # -----------------------------------------------------

    internship_id = db.Column(
        db.Integer,
        db.ForeignKey("internships.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # WEEK
    # -----------------------------------------------------

    week_number = db.Column(
        db.Integer,
        nullable=False
    )

    # -----------------------------------------------------
    # DATE COVERED
    # -----------------------------------------------------

    date_covered_start = db.Column(
        db.Date
    )

    date_covered_end = db.Column(
        db.Date
    )

    # -----------------------------------------------------
    # FILE
    # -----------------------------------------------------

    file_path = db.Column(
        db.String(255)
    )

    # -----------------------------------------------------
    # NOTES
    # -----------------------------------------------------

    notes = db.Column(
        db.Text
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = db.Column(
        db.String(20),
        default=STATUS_SUBMITTED
    )

    # -----------------------------------------------------
    # SUBMISSION DATE
    # -----------------------------------------------------

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# NARRATIVE REPORT
# =========================================================

class NarrativeReport(db.Model):
    __tablename__ = "narrative_reports"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # INTERNSHIP
    # -----------------------------------------------------

    internship_id = db.Column(
        db.Integer,
        db.ForeignKey("internships.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    title = db.Column(
        db.String(200),
        nullable=False
    )

    # -----------------------------------------------------
    # FILE
    # -----------------------------------------------------

    file_path = db.Column(
        db.String(255)
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    # -----------------------------------------------------
    # SUBMISSION DATE
    # -----------------------------------------------------

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# EVALUATION
# =========================================================

class Evaluation(db.Model):
    __tablename__ = "evaluations"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # INTERNSHIP
    # -----------------------------------------------------

    internship_id = db.Column(
        db.Integer,
        db.ForeignKey("internships.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # EVALUATOR
    # -----------------------------------------------------

    evaluator_name = db.Column(
        db.String(120)
    )

    evaluator_role = db.Column(
        db.String(50)
    )

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    score = db.Column(
        db.Numeric(5, 2)
    )

    # -----------------------------------------------------
    # REMARKS
    # -----------------------------------------------------

    remarks = db.Column(
        db.Text
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = db.Column(
        db.String(20),
        default="Not Started"
    )

    # -----------------------------------------------------
    # SUBMITTED DATE
    # -----------------------------------------------------

    submitted_at = db.Column(
        db.DateTime
    )


# =========================================================
# CERTIFICATE
# =========================================================

class Certificate(db.Model):
    __tablename__ = "certificates"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # INTERNSHIP
    # -----------------------------------------------------

    internship_id = db.Column(
        db.Integer,
        db.ForeignKey("internships.id"),
        unique=True,
        nullable=False
    )

    # -----------------------------------------------------
    # SIGNATORIES
    # -----------------------------------------------------

    supervisor_name = db.Column(
        db.String(120)
    )

    coordinator_name = db.Column(
        db.String(120)
    )

    dean_name = db.Column(
        db.String(120)
    )

    # -----------------------------------------------------
    # DATE ISSUED
    # -----------------------------------------------------

    date_issued = db.Column(
        db.Date
    )

    # -----------------------------------------------------
    # REQUIREMENTS
    # -----------------------------------------------------

    requirements_met = db.Column(
        db.Boolean,
        default=False
    )

    hours_met = db.Column(
        db.Boolean,
        default=False
    )

    evaluations_met = db.Column(
        db.Boolean,
        default=False
    )

    reports_met = db.Column(
        db.Boolean,
        default=False
    )

    endorsement_met = db.Column(
        db.Boolean,
        default=False
    )

    # -----------------------------------------------------
    # CERTIFICATE FILE ray allen viado hernandez
    # -----------------------------------------------------

    pdf_path = db.Column(
        db.String(255)
    )

    # -----------------------------------------------------
    # COMPLETED CERTIFICATE IMAGE
    # -----------------------------------------------------

    certificate_image_path = db.Column(
        db.String(255),
        nullable=True
    )

    # -----------------------------------------------------
    # CERTIFICATE READY STATUS
    # -----------------------------------------------------

    @property
    def is_ready(self):

        return all([
            self.requirements_met,
            self.hours_met,
            self.evaluations_met,
            self.reports_met,
            self.endorsement_met,
        ])


# =========================================================
# ANNOUNCEMENT
# =========================================================

class Announcement(db.Model):
    __tablename__ = "announcements"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # ANNOUNCEMENT INFORMATION
    # -----------------------------------------------------

    title = db.Column(
        db.String(200),
        nullable=False
    )

    body = db.Column(
        db.Text
    )

    # -----------------------------------------------------
    # DATE POSTED
    # -----------------------------------------------------

    posted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------------------
    # POSTED BY
    # -----------------------------------------------------

    posted_by = db.Column(
        db.String(120)
    )


# =========================================================
# NOTIFICATION
# =========================================================

class Notification(db.Model):
    __tablename__ = "notifications"

    # -----------------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    message = db.Column(
        db.String(255),
        nullable=False
    )

    # -----------------------------------------------------
    # READ STATUS
    # -----------------------------------------------------

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    # -----------------------------------------------------
    # CREATED DATE
    # -----------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )