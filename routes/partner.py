from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from flask_login import login_required, current_user

from decorators import role_required
from extensions import db

from models import (
    InternshipApplication,
    Internship,
    Evaluation,
)


partner_bp = Blueprint("partner", __name__)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _get_company():
    """
    Get the company profile belonging to the logged-in
    industry partner.
    """

    return current_user.partner_profile


def _get_company_interns(company):
    """
    Get all internship placements belonging to this partner's
    company.
    """

    if not company:
        return []

    return (
        Internship.query
        .filter_by(
            company_id=company.id
        )
        .order_by(
            Internship.id.desc()
        )
        .all()
    )


def _get_partner_evaluation(internship):
    """
    Get the latest evaluation created by the industry partner
    for the specified internship.

    Adviser evaluations are kept separate because their
    evaluator_role is 'Adviser'.
    """

    return (
        Evaluation.query
        .filter_by(
            internship_id=internship.id,
            evaluator_role="Supervisor",
        )
        .order_by(
            Evaluation.id.desc()
        )
        .first()
    )


def _partner_name():
    """
    Build the logged-in partner's full name.
    """

    parts = [
        current_user.first_name,
        current_user.middle_name,
        current_user.last_name,
    ]

    return " ".join(
        part
        for part in parts
        if part
    ).strip()


# =========================================================
# PARTNER DASHBOARD
# =========================================================

@partner_bp.route("/dashboard")
@login_required
@role_required("partner")
def dashboard():

    company = _get_company()

    interns = (
        _get_company_interns(company)
        if company
        else []
    )

    pending_applications = []

    if company:

        pending_applications = (
            InternshipApplication.query
            .filter_by(
                company_id=company.id,
                status=InternshipApplication.STATUS_PENDING
            )
            .order_by(
                InternshipApplication.submitted_at.desc()
            )
            .all()
        )

    return render_template(
        "partner/dashboard.html",
        company=company,
        interns=interns,
        pending_applications=pending_applications,
    )


# =========================================================
# APPLICATIONS
# =========================================================

@partner_bp.route("/applications")
@login_required
@role_required("partner")
def applications():

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    applications = (
        InternshipApplication.query
        .filter_by(
            company_id=company.id
        )
        .order_by(
            InternshipApplication.submitted_at.desc()
        )
        .all()
    )

    return render_template(
        "partner/applications.html",
        company=company,
        applications=applications,
    )


# =========================================================
# VIEW APPLICATION
# =========================================================

@partner_bp.route(
    "/applications/<int:application_id>"
)
@login_required
@role_required("partner")
def application_details(application_id):

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    application = (
        InternshipApplication.query
        .get_or_404(application_id)
    )

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    if application.company_id != company.id:

        flash(
            "You are not authorized to view this application.",
            "error"
        )

        return redirect(
            url_for("partner.applications")
        )

    return render_template(
        "partner/application_details.html",
        company=company,
        application=application,
    )


# =========================================================
# ACCEPT APPLICATION
# =========================================================

@partner_bp.route(
    "/applications/<int:application_id>/accept",
    methods=["POST"]
)
@login_required
@role_required("partner")
def accept_application(application_id):

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    application = (
        InternshipApplication.query
        .get_or_404(application_id)
    )

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    if application.company_id != company.id:

        flash(
            "You are not authorized to process this application.",
            "error"
        )

        return redirect(
            url_for("partner.applications")
        )

    # -----------------------------------------------------
    # ALREADY PROCESSED
    # -----------------------------------------------------

    if application.status != (
        InternshipApplication.STATUS_PENDING
    ):

        flash(
            "This application has already been processed.",
            "warning"
        )

        return redirect(
            url_for(
                "partner.application_details",
                application_id=application.id
            )
        )

    # -----------------------------------------------------
    # AVAILABLE SLOTS
    # -----------------------------------------------------

    if (
        company.available_slots is not None
        and company.available_slots <= 0
    ):

        flash(
            "There are no available internship slots for your company.",
            "error"
        )

        return redirect(
            url_for(
                "partner.application_details",
                application_id=application.id
            )
        )

    student = application.student

    # -----------------------------------------------------
    # CHECK EXISTING INTERNSHIP
    # -----------------------------------------------------

    existing_internship = (
        Internship.query
        .filter_by(
            student_id=student.id
        )
        .filter(
            Internship.status.in_([
                Internship.STATUS_ACTIVE,
                Internship.STATUS_ON_HOLD,
            ])
        )
        .first()
    )

    if existing_internship:

        flash(
            "This student already has an active or on-hold internship.",
            "warning"
        )

        return redirect(
            url_for(
                "partner.application_details",
                application_id=application.id
            )
        )

    # -----------------------------------------------------
    # ACCEPT
    # -----------------------------------------------------

    application.status = (
        InternshipApplication.STATUS_ACCEPTED
    )

    application.reviewed_at = datetime.utcnow()

    # -----------------------------------------------------
    # CREATE INTERNSHIP
    # -----------------------------------------------------

    internship = Internship(
        student_id=student.id,
        company_id=company.id,
        status=Internship.STATUS_ACTIVE,
        required_hours=240,
        completed_hours=0,
    )

    db.session.add(
        internship
    )

    # -----------------------------------------------------
    # REDUCE AVAILABLE SLOTS
    # -----------------------------------------------------

    if company.available_slots is not None:

        company.available_slots -= 1

    db.session.commit()

    flash(
        "The student's internship application has been accepted.",
        "success"
    )

    return redirect(
        url_for(
            "partner.application_details",
            application_id=application.id
        )
    )


# =========================================================
# REJECT APPLICATION
# =========================================================

@partner_bp.route(
    "/applications/<int:application_id>/reject",
    methods=["POST"]
)
@login_required
@role_required("partner")
def reject_application(application_id):

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    application = (
        InternshipApplication.query
        .get_or_404(application_id)
    )

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    if application.company_id != company.id:

        flash(
            "You are not authorized to process this application.",
            "error"
        )

        return redirect(
            url_for("partner.applications")
        )

    # -----------------------------------------------------
    # ALREADY PROCESSED
    # -----------------------------------------------------

    if application.status != (
        InternshipApplication.STATUS_PENDING
    ):

        flash(
            "This application has already been processed.",
            "warning"
        )

        return redirect(
            url_for(
                "partner.application_details",
                application_id=application.id
            )
        )

    application.status = (
        InternshipApplication.STATUS_REJECTED
    )

    application.reviewed_at = datetime.utcnow()

    db.session.commit()

    flash(
        "The student's internship application has been rejected.",
        "success"
    )

    return redirect(
        url_for(
            "partner.application_details",
            application_id=application.id
        )
    )


# =========================================================
# MY INTERNS
# =========================================================

@partner_bp.route("/interns")
@login_required
@role_required("partner")
def interns():

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    interns = _get_company_interns(
        company
    )

    return render_template(
        "partner/interns.html",
        company=company,
        interns=interns,
    )


# =========================================================
# EVALUATION LIST
# =========================================================

@partner_bp.route("/evaluation")
@login_required
@role_required("partner")
def evaluation():

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    interns = _get_company_interns(
        company
    )

    evaluation_records = []

    for internship in interns:

        eval_record = _get_partner_evaluation(
            internship
        )

        evaluation_records.append(
            {
                "internship": internship,
                "evaluation": eval_record,
            }
        )

    return render_template(
        "partner/evaluation.html",
        company=company,
        evaluation_records=evaluation_records,
    )


# =========================================================
# CREATE / EDIT EVALUATION
# =========================================================

@partner_bp.route(
    "/evaluation/<int:internship_id>",
    methods=["GET", "POST"]
)
@login_required
@role_required("partner")
def evaluation_form(internship_id):

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    internship = (
        Internship.query
        .filter_by(
            id=internship_id,
            company_id=company.id,
        )
        .first_or_404()
    )

    student = internship.student

    evaluation = _get_partner_evaluation(
        internship
    )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        score_text = request.form.get(
            "score",
            ""
        ).strip()

        remarks = request.form.get(
            "remarks",
            ""
        ).strip()

        # -------------------------------------------------
        # SCORE REQUIRED
        # -------------------------------------------------

        if not score_text:

            flash(
                "Please enter an evaluation score.",
                "error"
            )

            return render_template(
                "partner/evaluation_form.html",
                company=company,
                internship=internship,
                student=student,
                evaluation=evaluation,
            )

        # -------------------------------------------------
        # SCORE VALIDATION
        # -------------------------------------------------

        try:

            score = float(
                score_text
            )

        except ValueError:

            flash(
                "The evaluation score must be a valid number.",
                "error"
            )

            return render_template(
                "partner/evaluation_form.html",
                company=company,
                internship=internship,
                student=student,
                evaluation=evaluation,
            )

        if score < 0 or score > 100:

            flash(
                "The evaluation score must be between 0 and 100.",
                "error"
            )

            return render_template(
                "partner/evaluation_form.html",
                company=company,
                internship=internship,
                student=student,
                evaluation=evaluation,
            )

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        if evaluation is None:

            evaluation = Evaluation(
                internship_id=internship.id,
                evaluator_name=_partner_name(),
                evaluator_role="Supervisor",
                score=score,
                remarks=remarks,
                status="Submitted",
                submitted_at=datetime.utcnow(),
            )

            db.session.add(
                evaluation
            )

            message = (
                "The student's evaluation has been submitted successfully."
            )

        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        else:

            evaluation.evaluator_name = (
                _partner_name()
            )

            evaluation.evaluator_role = (
                "Supervisor"
            )

            evaluation.score = score

            evaluation.remarks = remarks

            evaluation.status = (
                "Submitted"
            )

            evaluation.submitted_at = (
                datetime.utcnow()
            )

            message = (
                "The student's evaluation has been updated successfully."
            )

        db.session.commit()

        flash(
            message,
            "success"
        )

        return redirect(
            url_for(
                "partner.evaluation"
            )
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "partner/evaluation_form.html",
        company=company,
        internship=internship,
        student=student,
        evaluation=evaluation,
    )


# =========================================================
# FEEDBACK LIST
# =========================================================

@partner_bp.route("/feedback")
@login_required
@role_required("partner")
def feedback():

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    interns = _get_company_interns(
        company
    )

    feedback_records = []

    for internship in interns:

        evaluation = _get_partner_evaluation(
            internship
        )

        feedback_records.append(
            {
                "internship": internship,
                "evaluation": evaluation,
            }
        )

    return render_template(
        "partner/feedback.html",
        company=company,
        feedback_records=feedback_records,
    )


# =========================================================
# ADD / EDIT FEEDBACK
# =========================================================

@partner_bp.route(
    "/feedback/<int:internship_id>",
    methods=["GET", "POST"]
)
@login_required
@role_required("partner")
def feedback_form(internship_id):

    company = _get_company()

    if not company:

        flash(
            "Your company profile was not found.",
            "error"
        )

        return redirect(
            url_for("partner.dashboard")
        )

    internship = (
        Internship.query
        .filter_by(
            id=internship_id,
            company_id=company.id,
        )
        .first_or_404()
    )

    student = internship.student

    evaluation = _get_partner_evaluation(
        internship
    )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        remarks = request.form.get(
            "remarks",
            ""
        ).strip()

        if not remarks:

            flash(
                "Please enter your feedback for the student.",
                "error"
            )

            return render_template(
                "partner/feedback_form.html",
                company=company,
                internship=internship,
                student=student,
                evaluation=evaluation,
            )

        # -------------------------------------------------
        # CREATE EVALUATION RECORD WHEN NEEDED
        # -------------------------------------------------

        if evaluation is None:

            evaluation = Evaluation(
                internship_id=internship.id,
                evaluator_name=_partner_name(),
                evaluator_role="Supervisor",
                score=None,
                remarks=remarks,
                status="Submitted",
                submitted_at=datetime.utcnow(),
            )

            db.session.add(
                evaluation
            )

        # -------------------------------------------------
        # UPDATE EXISTING RECORD
        # -------------------------------------------------

        else:

            evaluation.evaluator_name = (
                _partner_name()
            )

            evaluation.evaluator_role = (
                "Supervisor"
            )

            evaluation.remarks = remarks

            evaluation.status = (
                "Submitted"
            )

            evaluation.submitted_at = (
                datetime.utcnow()
            )

        db.session.commit()

        flash(
            "Feedback has been saved successfully.",
            "success"
        )

        return redirect(
            url_for(
                "partner.feedback"
            )
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "partner/feedback_form.html",
        company=company,
        internship=internship,
        student=student,
        evaluation=evaluation,
    )