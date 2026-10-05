import os
import re
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
)

from flask_login import login_required, current_user
from extensions import db
from decorators import role_required

from models import (
    User,
    StudentProfile,
    IndustryPartner,
    Internship,
    InternshipApplication,
    WeeklyReport,
    NarrativeReport,
    Evaluation,
    Notification,
)


admin_bp = Blueprint(
    "admin",
    __name__
)


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_bp.route("/dashboard")
@login_required
@role_required(User.ROLE_ADMIN)
def dashboard():

    # -----------------------------------------------------
    # TOTAL STUDENTS
    # -----------------------------------------------------

    total_students = (
        StudentProfile.query.count()
    )

    # -----------------------------------------------------
    # ACTIVE INTERNS
    # -----------------------------------------------------

    active_interns = (
        Internship.query
        .filter_by(
            status=Internship.STATUS_ACTIVE
        )
        .count()
    )

    # -----------------------------------------------------
    # PARTNER COMPANIES
    # -----------------------------------------------------

    partner_companies = (
        IndustryPartner.query
        .filter_by(
            status="Active"
        )
        .count()
    )

    # -----------------------------------------------------
    # PENDING WEEKLY REPORTS
    # -----------------------------------------------------

    pending_reports = (
        WeeklyReport.query
        .filter(
            WeeklyReport.status.in_([
                WeeklyReport.STATUS_SUBMITTED,
                WeeklyReport.STATUS_PENDING,
            ])
        )
        .count()
    )

    # -----------------------------------------------------
    # PENDING ACCOUNTS
    # -----------------------------------------------------

    pending_accounts = (
        User.query
        .filter(
            User.role.in_([
                User.ROLE_STUDENT,
                User.ROLE_PARTNER,
            ]),
            User.approval_status == User.APPROVAL_PENDING,
        )
        .count()
    )

    # -----------------------------------------------------
    # STUDENTS OVERVIEW
    # -----------------------------------------------------

    students_overview = (
        Internship.query
        .order_by(
            Internship.id.desc()
        )
        .limit(10)
        .all()
    )

    # -----------------------------------------------------
    # COMPANIES OVERVIEW
    # -----------------------------------------------------

    companies_overview = (
        IndustryPartner.query
        .order_by(
            IndustryPartner.company_name.asc()
        )
        .limit(10)
        .all()
    )

    # -----------------------------------------------------
    # RECENT WEEKLY REPORTS
    # -----------------------------------------------------

    recent_weekly_reports = (
        WeeklyReport.query
        .order_by(
            WeeklyReport.submitted_at.desc()
        )
        .limit(10)
        .all()
    )

    # -----------------------------------------------------
    # RECENT EVALUATIONS
    # -----------------------------------------------------

    recent_evaluations = (
        Evaluation.query
        .order_by(
            Evaluation.id.desc()
        )
        .limit(10)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        active_interns=active_interns,
        partner_companies=partner_companies,
        pending_reports=pending_reports,
        pending_accounts=pending_accounts,
        students_overview=students_overview,
        companies_overview=companies_overview,
        recent_weekly_reports=recent_weekly_reports,
        recent_evaluations=recent_evaluations,
    )


# =========================================================
# ACCOUNT APPROVALS
# =========================================================

@admin_bp.route("/account-approvals")
@login_required
@role_required(User.ROLE_ADMIN)
def account_approvals():

    users = (
        User.query
        .filter(
            User.role.in_([
                User.ROLE_STUDENT,
                User.ROLE_PARTNER,
            ])
        )
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin/account_approvals.html",
        users=users
    )


# =========================================================
# VIEW VERIFICATION DOCUMENT
# =========================================================

@admin_bp.route(
    "/account-approvals/<int:user_id>/document"
)
@login_required
@role_required(User.ROLE_ADMIN)
def view_verification_document(user_id):

    user = User.query.get_or_404(
        user_id
    )

    if not user.verification_document_path:

        flash(
            "No verification document was uploaded.",
            "warning"
        )

        return redirect(
            url_for(
                "admin.account_approvals"
            )
        )

    file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        user.verification_document_path
    )

    if not os.path.exists(file_path):

        flash(
            "The verification document could not be found.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.account_approvals"
            )
        )

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        user.verification_document_path,
        as_attachment=False
    )


# =========================================================
# APPROVE ACCOUNT
# =========================================================

@admin_bp.route(
    "/account-approvals/<int:user_id>/approve",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADMIN)
def approve_account(user_id):

    user = User.query.get_or_404(
        user_id
    )

    # -----------------------------------------------------
    # ADMIN ACCOUNT CHECK
    # -----------------------------------------------------

    if user.role == User.ROLE_ADMIN:

        flash(
            "Administrator accounts do not require approval.",
            "warning"
        )

        return redirect(
            url_for(
                "admin.account_approvals"
            )
        )

    # -----------------------------------------------------
    # VERIFICATION DOCUMENT CHECK
    # -----------------------------------------------------

    if not user.verification_document_path:

        flash(
            "This account cannot be approved without a verification document.",
            "error"
        )

        return redirect(
            url_for(
                "admin.account_approvals"
            )
        )

    # -----------------------------------------------------
    # APPROVE ACCOUNT
    # -----------------------------------------------------

    user.approval_status = (
        User.APPROVAL_APPROVED
    )

    user.is_active_account = True

    db.session.commit()

    flash(
        f"{user.full_name}'s account has been approved.",
        "success"
    )

    return redirect(
        url_for(
            "admin.account_approvals"
        )
    )


# =========================================================
# REJECT ACCOUNT
# =========================================================

@admin_bp.route(
    "/account-approvals/<int:user_id>/reject",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADMIN)
def reject_account(user_id):

    user = User.query.get_or_404(
        user_id
    )

    # -----------------------------------------------------
    # ADMIN ACCOUNT CHECK
    # -----------------------------------------------------

    if user.role == User.ROLE_ADMIN:

        flash(
            "Administrator accounts cannot be rejected here.",
            "warning"
        )

        return redirect(
            url_for(
                "admin.account_approvals"
            )
        )

    # -----------------------------------------------------
    # REJECT ACCOUNT
    # -----------------------------------------------------

    user.approval_status = (
        User.APPROVAL_REJECTED
    )

    user.is_active_account = False

    db.session.commit()

    flash(
        f"{user.full_name}'s account has been rejected.",
        "warning"
    )

    return redirect(
        url_for(
            "admin.account_approvals"
        )
    )


# =========================================================
# ADVISER MANAGEMENT
# =========================================================

@admin_bp.route("/advisers")
@login_required
@role_required(User.ROLE_ADMIN)
def advisers():

    # -----------------------------------------------------
    # GET ALL ADVISER ACCOUNTS
    # -----------------------------------------------------

    adviser_users = (
        User.query
        .filter_by(
            role=User.ROLE_ADVISER
        )
        .order_by(
            User.last_name.asc(),
            User.first_name.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # COUNT ASSIGNED STUDENTS
    # -----------------------------------------------------

    assigned_counts = {}

    for adviser in adviser_users:

        assigned_counts[adviser.id] = (
            StudentProfile.query
            .filter_by(
                adviser_id=adviser.id
            )
            .count()
        )

    # -----------------------------------------------------
    # EMPTY FORM FOR THE ADVISER PAGE
    # -----------------------------------------------------

    form = {
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "email": "",
        "contact_number": "",
    }

    # -----------------------------------------------------
    # DISPLAY PAGE
    # -----------------------------------------------------

    return render_template(
        "admin/advisers.html",
        advisers=adviser_users,
        assigned_counts=assigned_counts,
        form=form
    )


# =========================================================
# CREATE ADVISER ACCOUNT
# =========================================================

@admin_bp.route(
    "/advisers/create",
    methods=["GET", "POST"]
)
@login_required
@role_required(User.ROLE_ADMIN)
def create_adviser():

    form = {
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "email": "",
        "contact_number": "",
    }

    if request.method == "POST":

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        middle_name = request.form.get(
            "middle_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        contact_number = request.form.get(
            "contact_number",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        form = {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "email": email,
            "contact_number": contact_number,
        }

        # -------------------------------------------------
        # REQUIRED NAME FIELDS
        # -------------------------------------------------

        if not first_name or not last_name:

            flash(
                "First Name and Last Name are required.",
                "danger"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        # -------------------------------------------------
        # NAME VALIDATION
        # -------------------------------------------------

        name_pattern = (
            r"[A-Za-zÀ-ÖØ-öø-ÿ]+"
            r"(?:[ -][A-Za-zÀ-ÖØ-öø-ÿ]+)*"
        )

        for label, value in [
            ("First Name", first_name),
            ("Middle Name", middle_name),
            ("Last Name", last_name),
        ]:

            if value and not re.fullmatch(
                name_pattern,
                value
            ):

                flash(
                    f"{label} may contain letters, spaces, or hyphens only.",
                    "danger"
                )

                return render_template(
                    "admin/create_adviser.html",
                    form=form
                )

        # -------------------------------------------------
        # EMAIL VALIDATION
        # -------------------------------------------------

        email_pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        if not re.fullmatch(
            email_pattern,
            email
        ):

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        # -------------------------------------------------
        # PASSWORD VALIDATION
        # -------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        if len(password) > 30:

            flash(
                "Password must not exceed 30 characters.",
                "danger"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        # -------------------------------------------------
        # EMAIL DUPLICATE CHECK
        # -------------------------------------------------

        existing_user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if existing_user:

            flash(
                "That email address is already registered.",
                "warning"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        # -------------------------------------------------
        # CREATE APPROVED ACTIVE ADVISER
        # -------------------------------------------------

        adviser = User(
            first_name=first_name,
            middle_name=middle_name or None,
            last_name=last_name,
            email=email,
            contact_number=contact_number or None,
            role=User.ROLE_ADVISER,
            approval_status=User.APPROVAL_APPROVED,
            is_active_account=True,
            created_at=datetime.utcnow(),
        )

        adviser.set_password(
            password
        )

        db.session.add(
            adviser
        )

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "The Adviser account could not be created. Please try again.",
                "danger"
            )

            return render_template(
                "admin/create_adviser.html",
                form=form
            )

        flash(
            f"Adviser account for {adviser.full_name} was created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin.advisers"
            )
        )

    return render_template(
        "admin/create_adviser.html",
        form=form
    )


# =========================================================
# DELETE ADVISER ACCOUNT
# =========================================================

@admin_bp.route(
    "/advisers/<int:adviser_id>/delete",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADMIN)
def delete_adviser(adviser_id):

    adviser = User.query.get_or_404(
        adviser_id
    )

    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    if adviser.role != User.ROLE_ADVISER:

        flash(
            "Only Adviser accounts can be deleted from this page.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.advisers"
            )
        )

    # -----------------------------------------------------
    # PREVENT CURRENT USER FROM BEING DELETED
    # -----------------------------------------------------

    if adviser.id == current_user.id:

        flash(
            "You cannot delete the administrator account currently logged in.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.advisers"
            )
        )

    # -----------------------------------------------------
    # UNASSIGN STUDENTS FIRST
    # -----------------------------------------------------

    StudentProfile.query.filter_by(
        adviser_id=adviser.id
    ).update(
        {
            StudentProfile.adviser_id: None
        },
        synchronize_session=False
    )

    # -----------------------------------------------------
    # REMOVE NOTIFICATIONS FOR THE ADVISER
    # -----------------------------------------------------

    Notification.query.filter_by(
        user_id=adviser.id
    ).delete(
        synchronize_session=False
    )

    adviser_name = adviser.full_name

    # -----------------------------------------------------
    # DELETE ADVISER ACCOUNT
    # -----------------------------------------------------

    db.session.delete(
        adviser
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "The Adviser account could not be deleted because it is still being used by another record.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.advisers"
            )
        )

    flash(
        f"Adviser account for {adviser_name} was deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "admin.advisers"
        )
    )


# =========================================================
# ASSIGN OJT ADVISER
# =========================================================

@admin_bp.route(
    "/assign-adviser",
    methods=["GET", "POST"]
)
@login_required
@role_required(User.ROLE_ADMIN)
def assign_adviser():

    if request.method == "POST":

        student_id_text = request.form.get(
            "student_id",
            ""
        ).strip()

        adviser_id_text = request.form.get(
            "adviser_id",
            ""
        ).strip()

        # -------------------------------------------------
        # STUDENT ID VALIDATION
        # -------------------------------------------------

        try:

            student_id = int(
                student_id_text
            )

        except (ValueError, TypeError):

            flash(
                "Please select a valid student.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.assign_adviser"
                )
            )

        # -------------------------------------------------
        # ADVISER ID VALIDATION
        # -------------------------------------------------

        try:

            adviser_id = int(
                adviser_id_text
            )

        except (ValueError, TypeError):

            flash(
                "Please select a valid OJT Adviser.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.assign_adviser"
                )
            )

        # -------------------------------------------------
        # FIND APPROVED ACTIVE STUDENT
        # -------------------------------------------------

        student = (
            StudentProfile.query
            .join(
                User,
                StudentProfile.user_id == User.id
            )
            .filter(
                StudentProfile.id == student_id,
                User.role == User.ROLE_STUDENT,
                User.approval_status == User.APPROVAL_APPROVED,
                User.is_active_account.is_(True)
            )
            .first()
        )

        if student is None:

            flash(
                "The selected student is not approved or active.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.assign_adviser"
                )
            )

        # -------------------------------------------------
        # FIND APPROVED ACTIVE ADVISER
        # -------------------------------------------------

        adviser = (
            User.query
            .filter_by(
                id=adviser_id,
                role=User.ROLE_ADVISER,
                approval_status=User.APPROVAL_APPROVED,
                is_active_account=True,
            )
            .first()
        )

        if adviser is None:

            flash(
                "Selected Adviser is not approved or active.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.assign_adviser"
                )
            )

        # -------------------------------------------------
        # CHECK CURRENT ADVISER
        # -------------------------------------------------

        if student.adviser_id == adviser.id:

            flash(
                "This student is already assigned to that Adviser.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin.assign_adviser"
                )
            )

        # -------------------------------------------------
        # ASSIGN ADVISER
        # -------------------------------------------------

        old_adviser_id = student.adviser_id

        student.adviser_id = adviser.id

        db.session.commit()

        if old_adviser_id:

            flash(
                "The student's OJT Adviser has been reassigned successfully.",
                "success"
            )

        else:

            flash(
                "The student has been assigned to the OJT Adviser successfully.",
                "success"
            )

        return redirect(
            url_for(
                "admin.assign_adviser"
            )
        )

    # -----------------------------------------------------
    # GET APPROVED ACTIVE STUDENTS
    # -----------------------------------------------------

    students = (
        StudentProfile.query
        .join(
            User,
            StudentProfile.user_id == User.id
        )
        .filter(
            User.role == User.ROLE_STUDENT,
            User.approval_status == User.APPROVAL_APPROVED,
            User.is_active_account.is_(True)
        )
        .order_by(
            User.last_name.asc(),
            User.first_name.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # GET APPROVED ACTIVE ADVISERS
    # -----------------------------------------------------

    advisers = (
        User.query
        .filter_by(
            role=User.ROLE_ADVISER,
            approval_status=User.APPROVAL_APPROVED,
            is_active_account=True,
        )
        .order_by(
            User.last_name.asc(),
            User.first_name.asc()
        )
        .all()
    )

    return render_template(
        "admin/assign_adviser.html",
        students=students,
        advisers=advisers
    )


# =========================================================
# STUDENTS
# =========================================================

@admin_bp.route("/students")
@login_required
@role_required(User.ROLE_ADMIN)
def students():

    students = (
        StudentProfile.query
        .join(
            User,
            StudentProfile.user_id == User.id
        )
        .order_by(
            User.last_name.asc(),
            User.first_name.asc()
        )
        .all()
    )

    return render_template(
        "admin/students.html",
        students=students
    )


# =========================================================
# PARTNER COMPANIES
# =========================================================

@admin_bp.route("/partner-companies")
@login_required
@role_required(User.ROLE_ADMIN)
def partner_companies():

    companies = (
        IndustryPartner.query
        .order_by(
            IndustryPartner.company_name.asc()
        )
        .all()
    )

    return render_template(
        "admin/partner_companies.html",
        companies=companies
    )


# =========================================================
# ADD PARTNER COMPANY
# =========================================================

@admin_bp.route(
    "/partner-companies/add",
    methods=["GET", "POST"]
)
@login_required
@role_required(User.ROLE_ADMIN)
def add_partner_company():

    if request.method == "POST":

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        middle_name = request.form.get(
            "middle_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        contact_number = request.form.get(
            "contact_number",
            ""
        ).strip()

        company_name = request.form.get(
            "company_name",
            ""
        ).strip()

        industry = request.form.get(
            "industry",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        available_slots = request.form.get(
            "available_slots",
            type=int
        )

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not first_name:

            flash(
                "Please enter the partner's first name.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        if not last_name:

            flash(
                "Please enter the partner's last name.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        if not email:

            flash(
                "Please enter an email address.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        if not company_name:

            flash(
                "Please enter the company name.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        if not password or len(password) < 6:

            flash(
                "The password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        if len(password) > 30:

            flash(
                "The password must not exceed 30 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        if available_slots is None:

            available_slots = 0

        if available_slots < 0:

            flash(
                "Available slots cannot be negative.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        # -------------------------------------------------
        # EMAIL CHECK
        # -------------------------------------------------

        existing_user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if existing_user:

            flash(
                "That email address is already registered.",
                "warning"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        # -------------------------------------------------
        # CREATE PARTNER USER
        # -------------------------------------------------

        partner_user = User(
            first_name=first_name,
            middle_name=middle_name or None,
            last_name=last_name,
            email=email,
            contact_number=contact_number or None,
            role=User.ROLE_PARTNER,
            approval_status=User.APPROVAL_APPROVED,
            is_active_account=True,
        )

        partner_user.set_password(
            password
        )

        db.session.add(
            partner_user
        )

        try:

            db.session.flush()

            # -------------------------------------------------
            # CREATE COMPANY
            # -------------------------------------------------

            company = IndustryPartner(
                user_id=partner_user.id,
                company_name=company_name,
                industry=industry or None,
                address=address or None,
                available_slots=available_slots,
                status="Active",
            )

            db.session.add(
                company
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "The partner company could not be added. Please check the information and try again.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.add_partner_company"
                )
            )

        flash(
            f"{company_name} was added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin.partner_companies"
            )
        )

    return render_template(
        "admin/add_partner_company.html"
    )


# =========================================================
# REPORTS & MONITORING
# =========================================================

@admin_bp.route("/reports-monitoring")
@login_required
@role_required(User.ROLE_ADMIN)
def reports_monitoring():

    weekly_reports = (
        WeeklyReport.query
        .join(
            Internship,
            WeeklyReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .order_by(
            WeeklyReport.submitted_at.desc()
        )
        .all()
    )

    narrative_reports = (
        NarrativeReport.query
        .join(
            Internship,
            NarrativeReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .order_by(
            NarrativeReport.submitted_at.desc()
        )
        .all()
    )

    return render_template(
        "admin/reports_monitoring.html",
        weekly_reports=weekly_reports,
        narrative_reports=narrative_reports
    )


# =========================================================
# EVALUATIONS
# =========================================================

@admin_bp.route("/evaluations")
@login_required
@role_required(User.ROLE_ADMIN)
def evaluations():

    evaluations = (
        Evaluation.query
        .join(
            Internship,
            Evaluation.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .order_by(
            Evaluation.id.desc()
        )
        .all()
    )

    return render_template(
        "admin/evaluations.html",
        evaluations=evaluations
    )


# =========================================================
# GENERATE REPORT
# =========================================================

@admin_bp.route("/generate-report")
@login_required
@role_required(User.ROLE_ADMIN)
def generate_report():

    # -----------------------------------------------------
    # STUDENTS
    # -----------------------------------------------------

    total_students = (
        StudentProfile.query.count()
    )

    # -----------------------------------------------------
    # PARTNER COMPANIES
    # -----------------------------------------------------

    total_partner_companies = (
        IndustryPartner.query.count()
    )

    active_partner_companies = (
        IndustryPartner.query
        .filter_by(
            status="Active"
        )
        .count()
    )

    # -----------------------------------------------------
    # INTERNSHIPS
    # -----------------------------------------------------

    total_internships = (
        Internship.query.count()
    )

    active_internships = (
        Internship.query
        .filter_by(
            status=Internship.STATUS_ACTIVE
        )
        .count()
    )

    completed_internships = (
        Internship.query
        .filter_by(
            status=Internship.STATUS_COMPLETED
        )
        .count()
    )

    # -----------------------------------------------------
    # WEEKLY REPORTS
    # -----------------------------------------------------

    total_weekly_reports = (
        WeeklyReport.query.count()
    )

    submitted_weekly_reports = (
        WeeklyReport.query
        .filter_by(
            status=WeeklyReport.STATUS_SUBMITTED
        )
        .count()
    )

    approved_weekly_reports = (
        WeeklyReport.query
        .filter_by(
            status=WeeklyReport.STATUS_APPROVED
        )
        .count()
    )

    pending_weekly_reports = (
        WeeklyReport.query
        .filter_by(
            status=WeeklyReport.STATUS_PENDING
        )
        .count()
    )

    # -----------------------------------------------------
    # NARRATIVE REPORTS
    # -----------------------------------------------------

    total_narrative_reports = (
        NarrativeReport.query.count()
    )

    # -----------------------------------------------------
    # EVALUATIONS
    # -----------------------------------------------------

    total_evaluations = (
        Evaluation.query.count()
    )

    submitted_evaluations = (
        Evaluation.query
        .filter_by(
            status="Submitted"
        )
        .count()
    )

    return render_template(
        "admin/generate_report.html",
        total_students=total_students,
        total_partner_companies=total_partner_companies,
        active_partner_companies=active_partner_companies,
        total_internships=total_internships,
        active_internships=active_internships,
        completed_internships=completed_internships,
        total_weekly_reports=total_weekly_reports,
        submitted_weekly_reports=submitted_weekly_reports,
        approved_weekly_reports=approved_weekly_reports,
        pending_weekly_reports=pending_weekly_reports,
        total_narrative_reports=total_narrative_reports,
        total_evaluations=total_evaluations,
        submitted_evaluations=submitted_evaluations,
    )