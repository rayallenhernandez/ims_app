import os

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    send_from_directory,
)

from flask_login import login_required, current_user

from werkzeug.utils import secure_filename

from extensions import db

from models import (
    User,
    StudentProfile,
    Internship,
    WeeklyReport,
    NarrativeReport,
    Evaluation,
    Certificate,
    Attendance,
)

from decorators import role_required


adviser_bp = Blueprint("adviser", __name__)


# =========================================================
# ADVISER DASHBOARD
# =========================================================

@adviser_bp.route("/dashboard")
@login_required
@role_required(User.ROLE_ADVISER)
def dashboard():

    assigned_students_count = StudentProfile.query.filter_by(
        adviser_id=current_user.id
    ).count()

    assigned_internships_count = (
        Internship.query
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .count()
    )

    active_internships_count = (
        Internship.query
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id,
            Internship.status == "Active"
        )
        .count()
    )

    completed_internships_count = (
        Internship.query
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id,
            Internship.status == "Completed"
        )
        .count()
    )

    return render_template(
        "adviser/dashboard.html",
        adviser=current_user,
        assigned_students_count=assigned_students_count,
        assigned_internships_count=assigned_internships_count,
        active_internships_count=active_internships_count,
        completed_internships_count=completed_internships_count,
    )


# =========================================================
# ASSIGNED STUDENTS
# =========================================================

@adviser_bp.route("/students")
@login_required
@role_required(User.ROLE_ADVISER)
def students():

    students = (
        StudentProfile.query
        .filter_by(adviser_id=current_user.id)
        .join(
            User,
            StudentProfile.user_id == User.id
        )
        .order_by(
            User.last_name.asc()
        )
        .all()
    )

    return render_template(
        "adviser/students.html",
        students=students
    )


# =========================================================
# STUDENT DETAILS
# =========================================================

@adviser_bp.route("/students/<int:student_id>")
@login_required
@role_required(User.ROLE_ADVISER)
def student_details(student_id):

    student = StudentProfile.query.get_or_404(student_id)

    if student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this student.",
            "error"
        )

        return redirect(
            url_for("adviser.students")
        )

    internships = (
        Internship.query
        .filter_by(student_id=student.id)
        .order_by(Internship.id.desc())
        .all()
    )

    return render_template(
        "adviser/student_details.html",
        student=student,
        internships=internships
    )


# =========================================================
# INTERNSHIP MONITORING
# =========================================================

@adviser_bp.route("/internships")
@login_required
@role_required(User.ROLE_ADVISER)
def internships():

    internships = (
        Internship.query
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .order_by(
            Internship.id.desc()
        )
        .all()
    )

    evaluation_map = {}

    if internships:

        internship_ids = [
            internship.id
            for internship in internships
        ]

        evaluations = (
            Evaluation.query
            .filter(
                Evaluation.internship_id.in_(internship_ids)
            )
            .order_by(
                Evaluation.id.desc()
            )
            .all()
        )

        for evaluation in evaluations:

            if evaluation.internship_id not in evaluation_map:

                evaluation_map[
                    evaluation.internship_id
                ] = evaluation

    return render_template(
        "adviser/internships.html",
        internships=internships,
        evaluation_map=evaluation_map
    )


# =========================================================
# INTERNSHIP DETAILS
# =========================================================

@adviser_bp.route("/internships/<int:internship_id>")
@login_required
@role_required(User.ROLE_ADVISER)
def internship_details(internship_id):

    internship = Internship.query.get_or_404(
        internship_id
    )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this internship.",
            "error"
        )

        return redirect(
            url_for("adviser.internships")
        )

    attendances = (
        Attendance.query
        .filter_by(
            internship_id=internship.id
        )
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc()
        )
        .all()
    )

    return render_template(
        "adviser/internship_details.html",
        internship=internship,
        student=student,
        attendances=attendances
    )


# =========================================================
# OJT HOURS MONITORING
# =========================================================

@adviser_bp.route(
    "/students/<int:student_id>/hours"
)
@login_required
@role_required(User.ROLE_ADVISER)
def hours(student_id):

    student = StudentProfile.query.get_or_404(
        student_id
    )

    if student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this student's OJT hours.",
            "error"
        )

        return redirect(
            url_for("adviser.students")
        )

    internship = (
        Internship.query
        .filter_by(
            student_id=student.id
        )
        .order_by(
            Internship.id.desc()
        )
        .first()
    )

    if internship is None:

        flash(
            "This student does not have an internship placement yet.",
            "warning"
        )

        return redirect(
            url_for(
                "adviser.student_details",
                student_id=student.id
            )
        )

    attendances = (
        Attendance.query
        .filter_by(
            internship_id=internship.id
        )
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc()
        )
        .all()
    )

    active_attendance = (
        Attendance.query
        .filter_by(
            internship_id=internship.id,
            time_out=None
        )
        .order_by(
            Attendance.id.desc()
        )
        .first()
    )

    required_hours = internship.required_hours or 0
    completed_hours = internship.completed_hours or 0
    remaining_hours = max(
        required_hours - completed_hours,
        0
    )

    progress_percent = (
        min(
            round(
                (completed_hours / required_hours) * 100
            ),
            100
        )
        if required_hours > 0
        else 0
    )

    return render_template(
        "adviser/hours.html",
        adviser=current_user,
        student=student,
        internship=internship,
        attendances=attendances,
        active_attendance=active_attendance,
        required_hours=required_hours,
        completed_hours=completed_hours,
        remaining_hours=remaining_hours,
        progress_percent=progress_percent
    )


# =========================================================
# WEEKLY REPORTS
# =========================================================

@adviser_bp.route("/reports")
@login_required
@role_required(User.ROLE_ADVISER)
def reports():

    reports = (
        WeeklyReport.query
        .join(
            Internship,
            WeeklyReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .order_by(
            WeeklyReport.submitted_at.desc()
        )
        .all()
    )

    return render_template(
        "adviser/reports.html",
        reports=reports
    )


# =========================================================
# WEEKLY REPORT DETAILS
# =========================================================

@adviser_bp.route("/reports/<int:report_id>")
@login_required
@role_required(User.ROLE_ADVISER)
def report_details(report_id):

    report = WeeklyReport.query.get_or_404(
        report_id
    )

    internship = report.internship

    if not internship:

        flash(
            "The internship associated with this report could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this report.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    return render_template(
        "adviser/report_details.html",
        report=report,
        internship=internship,
        student=student
    )


# =========================================================
# VIEW WEEKLY REPORT FILE
# =========================================================

@adviser_bp.route(
    "/reports/<int:report_id>/file"
)
@login_required
@role_required(User.ROLE_ADVISER)
def view_report_file(report_id):

    report = WeeklyReport.query.get_or_404(
        report_id
    )

    internship = report.internship

    if not internship:

        flash(
            "The internship associated with this report could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this report file.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    if not report.file_path:

        flash(
            "No report file was uploaded.",
            "warning"
        )

        return redirect(
            url_for(
                "adviser.report_details",
                report_id=report.id
            )
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        report.file_path
    )

    if not os.path.exists(full_path):

        flash(
            "The uploaded report file could not be found.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.report_details",
                report_id=report.id
            )
        )

    extension = (
        report.file_path
        .rsplit(".", 1)[-1]
        .lower()
    )

    mime_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        report.file_path,
        as_attachment=False,
        mimetype=mime_types.get(
            extension,
            "application/octet-stream"
        )
    )


# =========================================================
# APPROVE WEEKLY REPORT
# =========================================================

@adviser_bp.route(
    "/reports/<int:report_id>/approve",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def approve_report(report_id):

    report = WeeklyReport.query.get_or_404(
        report_id
    )

    internship = report.internship

    if not internship:

        flash(
            "The internship associated with this report could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to review this report.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    if report.status not in [
        WeeklyReport.STATUS_SUBMITTED,
        WeeklyReport.STATUS_PENDING
    ]:

        flash(
            "This report cannot be approved in its current status.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.report_details",
                report_id=report.id
            )
        )

    report.status = WeeklyReport.STATUS_APPROVED

    db.session.commit()

    flash(
        "Weekly report has been approved.",
        "success"
    )

    return redirect(
        url_for(
            "adviser.report_details",
            report_id=report.id
        )
    )


# =========================================================
# RETURN WEEKLY REPORT
# =========================================================

@adviser_bp.route(
    "/reports/<int:report_id>/return",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def return_report(report_id):

    report = WeeklyReport.query.get_or_404(
        report_id
    )

    internship = report.internship

    if not internship:

        flash(
            "The internship associated with this report could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to review this report.",
            "error"
        )

        return redirect(
            url_for("adviser.reports")
        )

    if report.status not in [
        WeeklyReport.STATUS_SUBMITTED,
        WeeklyReport.STATUS_PENDING
    ]:

        flash(
            "This report cannot be returned in its current status.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.report_details",
                report_id=report.id
            )
        )

    report.status = WeeklyReport.STATUS_PENDING

    db.session.commit()

    flash(
        "Weekly report has been returned to the student for correction.",
        "success"
    )

    return redirect(
        url_for(
            "adviser.report_details",
            report_id=report.id
        )
    )


# =========================================================
# NARRATIVE REPORTS
# =========================================================

@adviser_bp.route("/narrative-reports")
@login_required
@role_required(User.ROLE_ADVISER)
def narrative_reports():

    reports = (
        NarrativeReport.query
        .join(
            Internship,
            NarrativeReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .order_by(
            NarrativeReport.submitted_at.desc(),
            NarrativeReport.id.desc()
        )
        .all()
    )

    return render_template(
        "adviser/narrative_reports.html",
        reports=reports
    )


# =========================================================
# VIEW NARRATIVE REPORT FILE
# =========================================================

@adviser_bp.route(
    "/narrative-reports/<int:report_id>/file"
)
@login_required
@role_required(User.ROLE_ADVISER)
def view_narrative_report_file(report_id):

    report = (
        NarrativeReport.query
        .join(
            Internship,
            NarrativeReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            NarrativeReport.id == report_id,
            StudentProfile.adviser_id == current_user.id
        )
        .first_or_404()
    )

    if not report.file_path:

        flash(
            "No narrative report file was uploaded.",
            "warning"
        )

        return redirect(
            url_for("adviser.narrative_reports")
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        report.file_path
    )

    if not os.path.exists(full_path):

        flash(
            "The uploaded narrative report file could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.narrative_reports")
        )

    extension = (
        report.file_path
        .rsplit(".", 1)[-1]
        .lower()
    )

    mime_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        report.file_path,
        as_attachment=False,
        mimetype=mime_types.get(
            extension,
            "application/octet-stream"
        )
    )


# =========================================================
# APPROVE NARRATIVE REPORT
# =========================================================

@adviser_bp.route(
    "/narrative-reports/<int:report_id>/approve",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def approve_narrative_report(report_id):

    report = (
        NarrativeReport.query
        .join(
            Internship,
            NarrativeReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            NarrativeReport.id == report_id,
            StudentProfile.adviser_id == current_user.id
        )
        .first_or_404()
    )

    report.status = "Approved"

    db.session.commit()

    flash(
        "Narrative report has been approved.",
        "success"
    )

    return redirect(
        url_for("adviser.narrative_reports")
    )


# =========================================================
# REJECT NARRATIVE REPORT
# =========================================================

@adviser_bp.route(
    "/narrative-reports/<int:report_id>/reject",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def reject_narrative_report(report_id):

    report = (
        NarrativeReport.query
        .join(
            Internship,
            NarrativeReport.internship_id == Internship.id
        )
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            NarrativeReport.id == report_id,
            StudentProfile.adviser_id == current_user.id
        )
        .first_or_404()
    )

    report.status = "Rejected"

    db.session.commit()

    flash(
        "Narrative report has been rejected.",
        "warning"
    )

    return redirect(
        url_for("adviser.narrative_reports")
    )


# =========================================================
# EVALUATIONS
# =========================================================

@adviser_bp.route("/evaluations")
@login_required
@role_required(User.ROLE_ADVISER)
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
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .order_by(
            Evaluation.id.desc()
        )
        .all()
    )

    internships = (
        Internship.query
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .order_by(
            Internship.id.desc()
        )
        .all()
    )

    return render_template(
        "adviser/evaluations.html",
        evaluations=evaluations,
        internships=internships
    )


# =========================================================
# CREATE EVALUATION
# =========================================================

@adviser_bp.route(
    "/evaluations/create/<int:internship_id>",
    methods=["GET", "POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def create_evaluation(internship_id):

    internship = Internship.query.get_or_404(
        internship_id
    )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to evaluate this student.",
            "error"
        )

        return redirect(
            url_for("adviser.evaluations")
        )

    existing_evaluation = (
        Evaluation.query
        .filter_by(
            internship_id=internship.id
        )
        .order_by(
            Evaluation.id.desc()
        )
        .first()
    )

    if request.method == "GET" and existing_evaluation:

        return redirect(
            url_for(
                "adviser.evaluation_details",
                evaluation_id=existing_evaluation.id
            )
        )

    if request.method == "POST":

        existing_evaluation = (
            Evaluation.query
            .filter_by(
                internship_id=internship.id
            )
            .order_by(
                Evaluation.id.desc()
            )
            .first()
        )

        if existing_evaluation:

            flash(
                "This internship has already been evaluated.",
                "error"
            )

            return redirect(
                url_for(
                    "adviser.evaluation_details",
                    evaluation_id=existing_evaluation.id
                )
            )

        score_text = request.form.get(
            "score",
            ""
        ).strip()

        remarks = request.form.get(
            "remarks",
            ""
        ).strip()

        if not score_text:

            flash(
                "Please enter an evaluation score.",
                "error"
            )

            return render_template(
                "adviser/evaluation_form.html",
                internship=internship,
                student=student,
                evaluation=None
            )

        try:

            score = float(score_text)

        except ValueError:

            flash(
                "Score must be a valid number.",
                "error"
            )

            return render_template(
                "adviser/evaluation_form.html",
                internship=internship,
                student=student,
                evaluation=None
            )

        if score < 0 or score > 100:

            flash(
                "Score must be between 0 and 100.",
                "error"
            )

            return render_template(
                "adviser/evaluation_form.html",
                internship=internship,
                student=student,
                evaluation=None
            )

        evaluation = Evaluation(
            internship_id=internship.id,

            evaluator_name=(
                f"{current_user.first_name} "
                f"{current_user.last_name}"
            ).strip(),

            evaluator_role="Adviser",

            score=score,

            remarks=remarks,

            status="Submitted",

            submitted_at=datetime.utcnow()
        )

        db.session.add(evaluation)

        db.session.commit()

        flash(
            "Evaluation has been submitted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "adviser.evaluation_details",
                evaluation_id=evaluation.id
            )
        )

    return render_template(
        "adviser/evaluation_form.html",
        internship=internship,
        student=student,
        evaluation=None
    )


# =========================================================
# EVALUATION DETAILS
# =========================================================

@adviser_bp.route(
    "/evaluations/<int:evaluation_id>"
)
@login_required
@role_required(User.ROLE_ADVISER)
def evaluation_details(evaluation_id):

    evaluation = Evaluation.query.get_or_404(
        evaluation_id
    )

    internship = evaluation.internship

    if not internship:

        flash(
            "The internship associated with this evaluation could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.evaluations")
        )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this evaluation.",
            "error"
        )

        return redirect(
            url_for("adviser.evaluations")
        )

    return render_template(
        "adviser/evaluation_details.html",
        evaluation=evaluation,
        internship=internship,
        student=student
    )


# =========================================================
# EDIT EVALUATION
# =========================================================

@adviser_bp.route(
    "/evaluations/<int:evaluation_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def edit_evaluation(evaluation_id):

    evaluation = Evaluation.query.get_or_404(
        evaluation_id
    )

    internship = evaluation.internship

    if not internship:

        flash(
            "The internship associated with this evaluation could not be found.",
            "error"
        )

        return redirect(
            url_for("adviser.evaluations")
        )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to edit this evaluation.",
            "error"
        )

        return redirect(
            url_for("adviser.evaluations")
        )

    if request.method == "POST":

        score_text = request.form.get(
            "score",
            ""
        ).strip()

        remarks = request.form.get(
            "remarks",
            ""
        ).strip()

        if not score_text:

            flash(
                "Please enter an evaluation score.",
                "error"
            )

            return render_template(
                "adviser/evaluation_form.html",
                internship=internship,
                student=student,
                evaluation=evaluation
            )

        try:

            score = float(score_text)

        except ValueError:

            flash(
                "Score must be a valid number.",
                "error"
            )

            return render_template(
                "adviser/evaluation_form.html",
                internship=internship,
                student=student,
                evaluation=evaluation
            )

        if score < 0 or score > 100:

            flash(
                "Score must be between 0 and 100.",
                "error"
            )

            return render_template(
                "adviser/evaluation_form.html",
                internship=internship,
                student=student,
                evaluation=evaluation
            )

        evaluation.score = score
        evaluation.remarks = remarks

        evaluation.evaluator_name = (
            f"{current_user.first_name} "
            f"{current_user.last_name}"
        ).strip()

        evaluation.evaluator_role = "Adviser"
        evaluation.status = "Submitted"
        evaluation.submitted_at = datetime.utcnow()

        db.session.commit()

        flash(
            "Evaluation has been updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "adviser.evaluation_details",
                evaluation_id=evaluation.id
            )
        )

    return render_template(
        "adviser/evaluation_form.html",
        internship=internship,
        student=student,
        evaluation=evaluation
    )


# =========================================================
# CERTIFICATE STATUS HELPER
# =========================================================

def _calculate_certificate_status(
    internship,
    certificate
):

    required_hours = internship.required_hours or 240
    completed_hours = internship.completed_hours or 0

    certificate.hours_met = (
        completed_hours >= required_hours
    )

    reports = WeeklyReport.query.filter_by(
        internship_id=internship.id
    ).all()

    approved_reports = [
        report
        for report in reports
        if report.status == WeeklyReport.STATUS_APPROVED
    ]

    certificate.reports_met = (
        len(reports) > 0
        and len(approved_reports) == len(reports)
    )

    evaluations = Evaluation.query.filter_by(
        internship_id=internship.id
    ).all()

    certificate.evaluations_met = (
        len(evaluations) > 0
        and any(
            evaluation.status == "Submitted"
            and evaluation.score is not None
            for evaluation in evaluations
        )
    )

    certificate.endorsement_met = bool(
        certificate.pdf_path
    )

    certificate.requirements_met = (
        certificate.hours_met
        and certificate.reports_met
        and certificate.evaluations_met
        and certificate.endorsement_met
    )

    return (
        required_hours,
        completed_hours,
        reports,
        evaluations,
    )


# =========================================================
# CERTIFICATE READINESS
# =========================================================

@adviser_bp.route("/certificates")
@login_required
@role_required(User.ROLE_ADVISER)
def certificates():

    internships = (
        Internship.query
        .join(
            StudentProfile,
            Internship.student_id == StudentProfile.id
        )
        .filter(
            StudentProfile.adviser_id == current_user.id
        )
        .order_by(
            Internship.id.desc()
        )
        .all()
    )

    certificate_records = []

    for internship in internships:

        certificate = Certificate.query.filter_by(
            internship_id=internship.id
        ).first()

        if not certificate:

            certificate = Certificate(
                internship_id=internship.id
            )

        (
            required_hours,
            completed_hours,
            reports,
            evaluations,
        ) = _calculate_certificate_status(
            internship,
            certificate
        )

        certificate_records.append({
            "internship": internship,
            "certificate": certificate,
            "required_hours": required_hours,
            "completed_hours": completed_hours,
            "reports": reports,
            "evaluations": evaluations,
        })

    return render_template(
        "adviser/certificate_readiness.html",
        certificate_records=certificate_records
    )


# =========================================================
# CERTIFICATE DETAILS
# =========================================================

@adviser_bp.route(
    "/certificates/<int:internship_id>"
)
@login_required
@role_required(User.ROLE_ADVISER)
def certificate_details(internship_id):

    internship = Internship.query.get_or_404(
        internship_id
    )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this certificate record.",
            "error"
        )

        return redirect(
            url_for("adviser.certificates")
        )

    certificate = Certificate.query.filter_by(
        internship_id=internship.id
    ).first()

    if not certificate:

        certificate = Certificate(
            internship_id=internship.id
        )

    (
        required_hours,
        completed_hours,
        reports,
        evaluations,
    ) = _calculate_certificate_status(
        internship,
        certificate
    )

    return render_template(
        "adviser/certificate_details.html",
        internship=internship,
        student=student,
        certificate=certificate,
        reports=reports,
        evaluations=evaluations,
        required_hours=required_hours,
        completed_hours=completed_hours,
    )


# =========================================================
# UPLOAD COMPLETED CERTIFICATE
# =========================================================

@adviser_bp.route(
    "/certificates/<int:internship_id>/upload",
    methods=["POST"]
)
@login_required
@role_required(User.ROLE_ADVISER)
def upload_certificate(internship_id):

    internship = Internship.query.get_or_404(
        internship_id
    )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to upload a certificate for this student.",
            "error"
        )

        return redirect(
            url_for("adviser.certificates")
        )

    certificate = Certificate.query.filter_by(
        internship_id=internship.id
    ).first()

    if not certificate:

        certificate = Certificate(
            internship_id=internship.id
        )

        db.session.add(certificate)

    (
        required_hours,
        completed_hours,
        reports,
        evaluations,
    ) = _calculate_certificate_status(
        internship,
        certificate
    )

    if not certificate.hours_met:

        flash(
            "The student has not completed the required internship hours.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    if not certificate.reports_met:

        flash(
            "Not all weekly reports have been approved.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    if not certificate.evaluations_met:

        flash(
            "The student still needs a completed evaluation.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    file = request.files.get(
        "certificate_file"
    )

    if not file or not file.filename:

        flash(
            "Please select the completed certificate image.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    original_filename = file.filename

    extension = (
        original_filename.rsplit(".", 1)[-1].lower()
        if "." in original_filename
        else ""
    )

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
    }

    if extension not in allowed_extensions:

        flash(
            "Invalid certificate file. "
            "Please upload a JPG, JPEG, or PNG image.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    safe_name = secure_filename(
        original_filename
    )

    if not safe_name:

        flash(
            "The selected certificate file has an invalid name.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d%H%M%S%f"
    )

    stored_filename = (
        f"certificate_{internship.id}_"
        f"{timestamp}_"
        f"{safe_name}"
    )

    certificate_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "certificates"
    )

    os.makedirs(
        certificate_folder,
        exist_ok=True
    )

    full_path = os.path.join(
        certificate_folder,
        stored_filename
    )

    file.save(
        full_path
    )

    new_relative_path = (
        f"certificates/{stored_filename}"
    )

    old_path = certificate.pdf_path

    if old_path:

        old_full_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            old_path
        )

        if (
            os.path.exists(old_full_path)
            and os.path.abspath(old_full_path)
            != os.path.abspath(full_path)
        ):

            try:
                os.remove(old_full_path)
            except OSError:
                pass

    certificate.pdf_path = new_relative_path

    certificate.date_issued = datetime.utcnow().date()

    certificate.endorsement_met = True

    certificate.requirements_met = (
        certificate.hours_met
        and certificate.reports_met
        and certificate.evaluations_met
        and certificate.endorsement_met
    )

    db.session.commit()

    flash(
        "Completed certificate uploaded successfully.",
        "success"
    )

    return redirect(
        url_for(
            "adviser.certificate_details",
            internship_id=internship.id
        )
    )


# =========================================================
# VIEW CERTIFICATE
# =========================================================

@adviser_bp.route(
    "/certificates/<int:internship_id>/view"
)
@login_required
@role_required(User.ROLE_ADVISER)
def view_certificate(internship_id):

    internship = Internship.query.get_or_404(
        internship_id
    )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to view this certificate.",
            "error"
        )

        return redirect(
            url_for("adviser.certificates")
        )

    certificate = Certificate.query.filter_by(
        internship_id=internship.id
    ).first()

    if (
        not certificate
        or not certificate.pdf_path
    ):

        flash(
            "No uploaded certificate was found.",
            "warning"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        certificate.pdf_path
    )

    if not os.path.exists(full_path):

        flash(
            "The certificate image could not be found.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    extension = (
        certificate.pdf_path
        .rsplit(".", 1)[-1]
        .lower()
    )

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        certificate.pdf_path,
        as_attachment=False,
        mimetype=mime_types.get(
            extension,
            "application/octet-stream"
        )
    )


# =========================================================
# DOWNLOAD CERTIFICATE
# =========================================================

@adviser_bp.route(
    "/certificates/<int:internship_id>/download"
)
@login_required
@role_required(User.ROLE_ADVISER)
def download_certificate(internship_id):

    internship = Internship.query.get_or_404(
        internship_id
    )

    student = internship.student

    if not student or student.adviser_id != current_user.id:

        flash(
            "You are not authorized to download this certificate.",
            "error"
        )

        return redirect(
            url_for("adviser.certificates")
        )

    certificate = Certificate.query.filter_by(
        internship_id=internship.id
    ).first()

    if (
        not certificate
        or not certificate.pdf_path
    ):

        flash(
            "No uploaded certificate was found.",
            "warning"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    full_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        certificate.pdf_path
    )

    if not os.path.exists(full_path):

        flash(
            "The certificate image could not be found.",
            "error"
        )

        return redirect(
            url_for(
                "adviser.certificate_details",
                internship_id=internship.id
            )
        )

    extension = (
        certificate.pdf_path
        .rsplit(".", 1)[-1]
        .lower()
    )

    mime_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        certificate.pdf_path,
        as_attachment=True,
        download_name=(
            f"Certificate_of_Completion.{extension}"
        ),
        mimetype=mime_types.get(
            extension,
            "application/octet-stream"
        )
    )