import os

from datetime import datetime, date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
    send_file,
)

from flask_login import login_required, current_user

from werkzeug.utils import secure_filename

from extensions import db

from decorators import role_required

from models import (
    WeeklyReport,
    NarrativeReport,
    Announcement,
    Evaluation,
    Internship,
    InternshipApplication,
    IndustryPartner,
    Certificate,
    Attendance,
)


student_bp = Blueprint("student", __name__)


# =========================================================
# FILE UPLOAD HELPERS
# =========================================================

def _allowed_file(filename):

    ext = (
        filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )

    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _save_upload(file_storage, subfolder):

    """
    Save an uploaded file under UPLOAD_FOLDER/subfolder
    and return its path relative to UPLOAD_FOLDER.
    """

    if not file_storage or file_storage.filename == "":
        return None

    if not _allowed_file(file_storage.filename):

        flash(
            f"'{file_storage.filename}' is not an accepted file type.",
            "danger",
        )

        return None

    filename = secure_filename(
        file_storage.filename
    )

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d%H%M%S%f"
    )

    stored_name = (
        f"{timestamp}_{filename}"
    )

    folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        subfolder,
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    file_path = os.path.join(
        folder,
        stored_name,
    )

    file_storage.save(
        file_path
    )

    return f"{subfolder}/{stored_name}"


# =========================================================
# STUDENT DOCUMENT CONFIGURATION
# =========================================================

STUDENT_DOCUMENTS = {
    "resume": {
        "field": "resume_path",
        "folder": "resumes",
        "label": "Resume",
    },

    "application_letter": {
        "field": "application_letter_path",
        "folder": "application_letters",
        "label": "Application Letter",
    },

    "medical_certificate": {
        "field": "medical_certificate_path",
        "folder": "medical_certificates",
        "label": "Medical Certificate",
    },
}


# =========================================================
# CURRENT INTERNSHIP
# =========================================================

def _current_internship():

    profile = current_user.student_profile

    if profile is None:
        return None

    return (
        profile.internships
        .order_by(
            Internship.id.desc()
        )
        .first()
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():

    internship = _current_internship()

    announcements = (
        Announcement.query
        .order_by(
            Announcement.posted_at.desc()
        )
        .limit(4)
        .all()
    )

    weekly_count = (
        internship.weekly_reports.count()
        if internship
        else 0
    )

    narrative_count = (
        internship.narrative_reports.count()
        if internship
        else 0
    )

    profile = current_user.student_profile

    application_count = 0

    if profile:

        application_count = (
            InternshipApplication.query
            .filter_by(
                student_id=profile.id
            )
            .count()
        )

    return render_template(
        "student/dashboard.html",
        internship=internship,
        announcements=announcements,
        weekly_count=weekly_count,
        narrative_count=narrative_count,
        application_count=application_count,
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

@student_bp.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
@role_required("student")
def profile():

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Your student profile has not been created yet.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    if request.method == "POST":

        current_user.first_name = request.form.get(
            "first_name",
            current_user.first_name,
        ).strip()

        current_user.last_name = request.form.get(
            "last_name",
            current_user.last_name,
        ).strip()

        current_user.contact_number = request.form.get(
            "contact_number",
            current_user.contact_number,
        ).strip()

        profile.address = request.form.get(
            "address",
            profile.address,
        ).strip()

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success",
        )

        return redirect(
            url_for("student.profile")
        )

    internship = _current_internship()

    return render_template(
        "student/profile.html",
        profile=profile,
        internship=internship,
    )


# =========================================================
# VIEW STUDENT DOCUMENT
# =========================================================

@student_bp.route(
    "/profile/document/<document_type>/view"
)
@login_required
@role_required("student")
def view_document(document_type):

    document = STUDENT_DOCUMENTS.get(
        document_type
    )

    if document is None:

        flash(
            "Invalid document type.",
            "danger",
        )

        return redirect(
            url_for("student.profile")
        )

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Student profile not found.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    file_path = getattr(
        profile,
        document["field"],
        None,
    )

    if not file_path:

        flash(
            f"No {document['label']} has been uploaded yet.",
            "warning",
        )

        return redirect(
            url_for("student.profile")
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        file_path,
    )

    if not os.path.exists(full_path):

        flash(
            f"The uploaded {document['label']} could not be found.",
            "danger",
        )

        return redirect(
            url_for("student.profile")
        )

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        file_path,
        as_attachment=False,
    )


# =========================================================
# REPLACE STUDENT DOCUMENT
# =========================================================

@student_bp.route(
    "/profile/document/<document_type>/replace",
    methods=["POST"],
)
@login_required
@role_required("student")
def replace_document(document_type):

    document = STUDENT_DOCUMENTS.get(
        document_type
    )

    if document is None:

        flash(
            "Invalid document type.",
            "danger",
        )

        return redirect(
            url_for("student.profile")
        )

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Student profile not found.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    uploaded_file = request.files.get(
        "file"
    )

    if not uploaded_file or uploaded_file.filename == "":

        flash(
            f"Please select a new {document['label'].lower()} file.",
            "warning",
        )

        return redirect(
            url_for("student.profile")
        )

    # -----------------------------------------------------
    # KEEP THE OLD FILE PATH
    # -----------------------------------------------------

    old_file_path = getattr(
        profile,
        document["field"],
        None,
    )

    # -----------------------------------------------------
    # SAVE THE NEW FILE FIRST
    # -----------------------------------------------------

    new_file_path = _save_upload(
        uploaded_file,
        document["folder"],
    )

    # If validation failed, _save_upload already showed
    # the appropriate message.
    if not new_file_path:

        return redirect(
            url_for("student.profile")
        )

    # -----------------------------------------------------
    # UPDATE THE DATABASE
    # -----------------------------------------------------

    setattr(
        profile,
        document["field"],
        new_file_path,
    )

    db.session.commit()

    # -----------------------------------------------------
    # DELETE THE OLD FILE ONLY AFTER THE NEW FILE
    # HAS BEEN SUCCESSFULLY SAVED AND THE DATABASE
    # HAS BEEN UPDATED
    # -----------------------------------------------------

    if old_file_path:

        old_full_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            old_file_path,
        )

        try:

            if os.path.exists(old_full_path):

                os.remove(
                    old_full_path
                )

        except OSError:

            # The new file is already active in the database,
            # so an old-file cleanup failure should not undo
            # the successful replacement.
            current_app.logger.warning(
                "Could not remove old student document: %s",
                old_full_path,
            )

    flash(
        f"{document['label']} replaced successfully.",
        "success",
    )

    return redirect(
        url_for("student.profile")
    )


# =========================================================
# ADD SKILL
# =========================================================

@student_bp.route(
    "/profile/add-skill",
    methods=["POST"]
)
@login_required
@role_required("student")
def add_skill():

    skill = request.form.get(
        "skill",
        "",
    ).strip()

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Student profile not found.",
            "danger",
        )

        return redirect(
            url_for("student.profile")
        )

    if skill:

        existing = profile.skills_list

        already_exists = any(
            existing_skill.lower() == skill.lower()
            for existing_skill in existing
        )

        if not already_exists:

            existing.append(
                skill
            )

            profile.skills = ", ".join(
                existing
            )

            db.session.commit()

            flash(
                "Skill added successfully.",
                "success",
            )

    return redirect(
        url_for("student.profile")
    )


# =========================================================
# AVAILABLE INTERNSHIP COMPANIES
# =========================================================

@student_bp.route("/companies")
@login_required
@role_required("student")
def companies():

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Your student profile has not been created yet.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    companies = (
        IndustryPartner.query
        .filter(
            IndustryPartner.status == "Active",
            IndustryPartner.available_slots > 0,
        )
        .order_by(
            IndustryPartner.company_name.asc()
        )
        .all()
    )

    existing_applications = (
        InternshipApplication.query
        .filter_by(
            student_id=profile.id
        )
        .all()
    )

    applied_company_ids = {
        application.company_id
        for application in existing_applications
    }

    return render_template(
        "student/companies.html",
        companies=companies,
        applied_company_ids=applied_company_ids,
    )


# =========================================================
# COMPANY DETAILS
# =========================================================

@student_bp.route(
    "/companies/<int:company_id>"
)
@login_required
@role_required("student")
def company_details(company_id):

    company = (
        IndustryPartner.query
        .filter_by(
            id=company_id,
            status="Active",
        )
        .first_or_404()
    )

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Your student profile has not been created yet.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    existing_application = (
        InternshipApplication.query
        .filter_by(
            student_id=profile.id,
            company_id=company.id,
        )
        .order_by(
            InternshipApplication.id.desc()
        )
        .first()
    )

    return render_template(
        "student/company_details.html",
        company=company,
        existing_application=existing_application,
    )


# =========================================================
# APPLY FOR INTERNSHIP
# =========================================================

@student_bp.route(
    "/companies/<int:company_id>/apply",
    methods=["GET", "POST"],
)
@login_required
@role_required("student")
def apply(company_id):

    company = (
        IndustryPartner.query
        .filter_by(
            id=company_id,
            status="Active",
        )
        .first_or_404()
    )

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Your student profile has not been created yet.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    if (
        company.available_slots is None
        or company.available_slots <= 0
    ):

        flash(
            "This company currently has no available internship slots.",
            "warning",
        )

        return redirect(
            url_for(
                "student.company_details",
                company_id=company.id,
            )
        )

    existing_application = (
        InternshipApplication.query
        .filter_by(
            student_id=profile.id,
            company_id=company.id,
        )
        .order_by(
            InternshipApplication.id.desc()
        )
        .first()
    )

    if existing_application:

        if existing_application.status == (
            InternshipApplication.STATUS_PENDING
        ):

            flash(
                "You already have a pending application for this company.",
                "warning",
            )

        elif existing_application.status == (
            InternshipApplication.STATUS_ACCEPTED
        ):

            flash(
                "Your application to this company has already been accepted.",
                "info",
            )

        else:

            flash(
                "You already applied to this company.",
                "warning",
            )

        return redirect(
            url_for(
                "student.company_details",
                company_id=company.id,
            )
        )

    if request.method == "POST":

        message = request.form.get(
            "message",
            "",
        ).strip()

        if not message:

            flash(
                "Please enter an application message.",
                "danger",
            )

            return render_template(
                "student/apply.html",
                company=company,
            )

        application = InternshipApplication(
            student_id=profile.id,
            company_id=company.id,
            status=InternshipApplication.STATUS_PENDING,
            message=message,
            submitted_at=datetime.utcnow(),
        )

        db.session.add(
            application
        )

        db.session.commit()

        flash(
            f"Your application to {company.company_name} "
            "has been submitted successfully. "
            "It is now pending company review.",
            "success",
        )

        return redirect(
            url_for("student.applications")
        )

    return render_template(
        "student/apply.html",
        company=company,
    )


# =========================================================
# STUDENT APPLICATIONS
# =========================================================

@student_bp.route("/applications")
@login_required
@role_required("student")
def applications():

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Your student profile has not been created yet.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    applications = (
        InternshipApplication.query
        .filter_by(
            student_id=profile.id
        )
        .order_by(
            InternshipApplication.submitted_at.desc()
        )
        .all()
    )

    return render_template(
        "student/applications.html",
        applications=applications,
    )


# =========================================================
# CANCEL PENDING APPLICATION
# =========================================================

@student_bp.route(
    "/applications/<int:application_id>/cancel",
    methods=["POST"],
)
@login_required
@role_required("student")
def cancel_application(application_id):

    profile = current_user.student_profile

    if profile is None:

        flash(
            "Student profile not found.",
            "danger",
        )

        return redirect(
            url_for("student.dashboard")
        )

    application = (
        InternshipApplication.query
        .filter_by(
            id=application_id,
            student_id=profile.id,
        )
        .first_or_404()
    )

    if application.status != (
        InternshipApplication.STATUS_PENDING
    ):

        flash(
            "Only pending applications can be cancelled.",
            "warning",
        )

        return redirect(
            url_for("student.applications")
        )

    db.session.delete(
        application
    )

    db.session.commit()

    flash(
        "Your internship application has been cancelled.",
        "success",
    )

    return redirect(
        url_for("student.applications")
    )


# =========================================================
# STUDENT REPORTS
# =========================================================

@student_bp.route(
    "/reports",
    methods=["GET", "POST"]
)
@login_required
@role_required("student")
def reports():

    internship = _current_internship()

    if request.method == "POST":

        if internship is None:

            flash(
                "You need an active internship placement "
                "before submitting reports.",
                "danger",
            )

            return redirect(
                url_for("student.reports")
            )

        report_kind = request.form.get(
            "report_kind"
        )

        # -------------------------------------------------
        # WEEKLY REPORT
        # -------------------------------------------------

        if report_kind == "weekly":

            week_number = request.form.get(
                "week_number",
                type=int,
            )

            notes = request.form.get(
                "notes",
                "",
            ).strip()

            file_path = _save_upload(
                request.files.get("file"),
                "weekly_reports",
            )

            if not week_number:

                flash(
                    "Please select a week number.",
                    "danger",
                )

            else:

                report = WeeklyReport(
                    internship_id=internship.id,
                    week_number=week_number,
                    notes=notes,
                    file_path=file_path,
                    status=WeeklyReport.STATUS_SUBMITTED,
                )

                db.session.add(
                    report
                )

                db.session.commit()

                flash(
                    f"Week {week_number} report submitted.",
                    "success",
                )

        # -------------------------------------------------
        # NARRATIVE REPORT
        # -------------------------------------------------

        elif report_kind == "narrative":

            title = request.form.get(
                "title",
                "",
            ).strip()

            file_path = _save_upload(
                request.files.get("file"),
                "narrative_reports",
            )

            if not title:

                flash(
                    "Please give the narrative report a title.",
                    "danger",
                )

            else:

                report = NarrativeReport(
                    internship_id=internship.id,
                    title=title,
                    file_path=file_path,
                    status="Pending",
                )

                db.session.add(
                    report
                )

                db.session.commit()

                flash(
                    "Narrative report submitted.",
                    "success",
                )

        return redirect(
            url_for("student.reports")
        )

    weekly_reports = (
        internship.weekly_reports
        .order_by(
            WeeklyReport.week_number
        )
        .all()
        if internship
        else []
    )

    narrative_reports = (
        internship.narrative_reports.all()
        if internship
        else []
    )

    return render_template(
        "student/reports.html",
        internship=internship,
        weekly_reports=weekly_reports,
        narrative_reports=narrative_reports,
    )


# =========================================================
# UPLOADED FILES
# =========================================================

@student_bp.route(
    "/uploads/<path:filepath>"
)
@login_required
def uploaded_file(filepath):

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filepath,
    )


# =========================================================
# CERTIFICATE STATUS
# =========================================================

def _get_certificate_status(internship):

    if internship is None:
        return None

    cert = Certificate.query.filter_by(
        internship_id=internship.id
    ).first()

    if cert is None:
        return None

    required_hours = (
        internship.required_hours or 240
    )

    completed_hours = (
        internship.completed_hours or 0
    )

    # -----------------------------------------------------
    # HOURS
    # -----------------------------------------------------

    cert.hours_met = (
        completed_hours >= required_hours
    )

    # -----------------------------------------------------
    # WEEKLY REPORTS
    # -----------------------------------------------------

    reports = WeeklyReport.query.filter_by(
        internship_id=internship.id
    ).all()

    approved_reports = [
        report
        for report in reports
        if report.status == WeeklyReport.STATUS_APPROVED
    ]

    cert.reports_met = (
        len(reports) > 0
        and len(approved_reports) == len(reports)
    )

    # -----------------------------------------------------
    # EVALUATIONS
    # -----------------------------------------------------

    evaluations = Evaluation.query.filter_by(
        internship_id=internship.id
    ).all()

    cert.evaluations_met = (
        len(evaluations) > 0
        and any(
            evaluation.status == "Submitted"
            and evaluation.score is not None
            for evaluation in evaluations
        )
    )

    # -----------------------------------------------------
    # CERTIFICATE UPLOAD
    # -----------------------------------------------------

    cert.endorsement_met = bool(
        cert.pdf_path
    )

    # -----------------------------------------------------
    # OVERALL REQUIREMENTS
    # -----------------------------------------------------

    cert.requirements_met = (
        cert.hours_met
        and cert.reports_met
        and cert.evaluations_met
        and cert.endorsement_met
    )

    return cert


# =========================================================
# STUDENT CERTIFICATE
# =========================================================

@student_bp.route("/certificate")
@login_required
@role_required("student")
def certificate():

    internship = _current_internship()

    if internship is None:

        return render_template(
            "student/certificate.html",
            internship=None,
            cert=None,
            required_hours=0,
            completed_hours=0,
            remaining_hours=0,
            progress_percent=0,
        )

    cert = _get_certificate_status(
        internship
    )

    required_hours = (
        internship.required_hours or 240
    )

    completed_hours = (
        internship.completed_hours or 0
    )

    remaining_hours = max(
        required_hours - completed_hours,
        0
    )

    if required_hours > 0:

        progress_percent = min(
            round(
                (
                    completed_hours
                    / required_hours
                ) * 100
            ),
            100
        )

    else:

        progress_percent = 0

    return render_template(
        "student/certificate.html",
        internship=internship,
        cert=cert,
        required_hours=required_hours,
        completed_hours=completed_hours,
        remaining_hours=remaining_hours,
        progress_percent=progress_percent,
    )


# =========================================================
# VIEW CERTIFICATE IMAGE - STUDENT
# =========================================================

@student_bp.route(
    "/certificate/view"
)
@login_required
@role_required("student")
def view_certificate():

    internship = _current_internship()

    if internship is None:

        flash(
            "No internship record was found.",
            "danger",
        )

        return redirect(
            url_for("student.certificate")
        )

    cert = Certificate.query.filter_by(
        internship_id=internship.id
    ).first()

    if not cert or not cert.pdf_path:

        flash(
            "Your completed certificate has not been uploaded yet.",
            "warning",
        )

        return redirect(
            url_for("student.certificate")
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        cert.pdf_path,
    )

    if not os.path.exists(full_path):

        flash(
            "The certificate image could not be found.",
            "danger",
        )

        return redirect(
            url_for("student.certificate")
        )

    extension = (
        cert.pdf_path
        .rsplit(".", 1)[-1]
        .lower()
    )

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    mimetype = mime_types.get(
        extension,
        "application/octet-stream",
    )

    return send_file(
        full_path,
        as_attachment=False,
        mimetype=mimetype,
    )


# =========================================================
# DOWNLOAD CERTIFICATE
# =========================================================

@student_bp.route(
    "/certificate/download"
)
@login_required
@role_required("student")
def download_certificate():

    internship = _current_internship()

    if internship is None:

        flash(
            "No internship record was found.",
            "danger",
        )

        return redirect(
            url_for("student.certificate")
        )

    cert = _get_certificate_status(
        internship
    )

    if cert is None:

        flash(
            "Your certificate has not been prepared yet.",
            "warning",
        )

        return redirect(
            url_for("student.certificate")
        )

    if not cert.is_ready:

        flash(
            "Your certificate is not ready yet. "
            "Please complete all requirements and wait "
            "for your adviser to upload the completed certificate.",
            "warning",
        )

        return redirect(
            url_for("student.certificate")
        )

    if not cert.pdf_path:

        flash(
            "Your completed certificate has not been uploaded yet.",
            "warning",
        )

        return redirect(
            url_for("student.certificate")
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        cert.pdf_path,
    )

    if not os.path.exists(full_path):

        flash(
            "The certificate image could not be found.",
            "danger",
        )

        return redirect(
            url_for("student.certificate")
        )

    extension = (
        cert.pdf_path
        .rsplit(".", 1)[-1]
        .lower()
    )

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    mimetype = mime_types.get(
        extension,
        "application/octet-stream",
    )

    return send_file(
        full_path,
        as_attachment=True,
        download_name=(
            f"Certificate_of_Completion.{extension}"
        ),
        mimetype=mimetype,
    )


# =========================================================
# STUDENT HOURS TRACKING
# =========================================================

@student_bp.route("/hours-tracking")
@login_required
@role_required("student")
def hours_tracking():

    internship = _current_internship()

    if internship is None:

        return render_template(
            "student/hours_tracking.html",
            internship=None,
            attendances=[],
            active_attendance=None,
        )

    attendances = (
        internship.attendances
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        )
        .all()
    )

    active_attendance = (
        Attendance.query
        .filter_by(
            internship_id=internship.id,
            time_out=None,
        )
        .order_by(
            Attendance.id.desc()
        )
        .first()
    )

    return render_template(
        "student/hours_tracking.html",
        internship=internship,
        attendances=attendances,
        active_attendance=active_attendance,
    )


# =========================================================
# TIME IN
# =========================================================

@student_bp.route(
    "/hours-tracking/time-in",
    methods=["POST"],
)
@login_required
@role_required("student")
def time_in():

    internship = _current_internship()

    if internship is None:

        flash(
            "You do not have an internship placement yet.",
            "danger",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    if internship.status != Internship.STATUS_ACTIVE:

        flash(
            "Time In is only available for an active internship.",
            "warning",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    active_attendance = (
        Attendance.query
        .filter_by(
            internship_id=internship.id,
            time_out=None,
        )
        .first()
    )

    if active_attendance:

        flash(
            "You are already timed in. Please Time Out first.",
            "warning",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    today = date.today()

    existing_today = (
        Attendance.query
        .filter_by(
            internship_id=internship.id,
            attendance_date=today,
        )
        .first()
    )

    if existing_today:

        flash(
            "You already have an attendance record for today.",
            "warning",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    attendance = Attendance(
        internship_id=internship.id,
        attendance_date=today,
        time_in=datetime.now(),
        time_out=None,
        hours_rendered=0,
        status=Attendance.STATUS_PRESENT,
    )

    db.session.add(
        attendance
    )

    db.session.commit()

    flash(
        "Time In recorded successfully.",
        "success",
    )

    return redirect(
        url_for("student.hours_tracking")
    )


# =========================================================
# TIME OUT
# =========================================================

@student_bp.route(
    "/hours-tracking/time-out",
    methods=["POST"],
)
@login_required
@role_required("student")
def time_out():

    internship = _current_internship()

    if internship is None:

        flash(
            "You do not have an internship placement yet.",
            "danger",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    attendance = (
        Attendance.query
        .filter_by(
            internship_id=internship.id,
            time_out=None,
        )
        .order_by(
            Attendance.id.desc()
        )
        .first()
    )

    if attendance is None:

        flash(
            "No active Time In record was found.",
            "warning",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    now = datetime.now()

    if attendance.time_in and now <= attendance.time_in:

        flash(
            "Time Out must be later than Time In.",
            "danger",
        )

        return redirect(
            url_for("student.hours_tracking")
        )

    attendance.time_out = now

    hours = attendance.calculate_hours()

    attendance.status = Attendance.STATUS_COMPLETED

    rendered_hours = int(
        round(float(hours or 0))
    )

    current_completed = (
        internship.completed_hours or 0
    )

    required_hours = (
        internship.required_hours or 240
    )

    internship.completed_hours = min(
        current_completed + rendered_hours,
        required_hours,
    )

    if internship.completed_hours >= required_hours:

        internship.status = Internship.STATUS_COMPLETED

    db.session.commit()

    flash(
        f"Time Out recorded successfully. "
        f"{float(hours or 0):.2f} hour(s) rendered.",
        "success",
    )

    return redirect(
        url_for("student.hours_tracking")
    )


# =========================================================
# STUDENT EVALUATION
# =========================================================

@student_bp.route("/evaluation")
@login_required
@role_required("student")
def evaluation():

    internship = _current_internship()

    if internship is None:

        return render_template(
            "student/evaluation.html",
            internship=None,
            evaluations=[]
        )

    evaluations = (
        Evaluation.query
        .filter_by(
            internship_id=internship.id
        )
        .order_by(
            Evaluation.id.desc()
        )
        .all()
    )

    return render_template(
        "student/evaluation.html",
        internship=internship,
        evaluations=evaluations
    )