from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
)

from flask_login import (
    login_required,
    current_user,
)

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from extensions import db

from models import (
    User,
    StudentProfile,
    InternshipApplication,
    Internship,
    WeeklyReport,
    NarrativeReport,
    Evaluation,
    Certificate,
    Notification,
)


notifications_bp = Blueprint(
    "notifications",
    __name__,
)


# =========================================================
# NOTIFICATION HELPER
# =========================================================

def add_notification(
    session,
    user_id,
    message,
):
    """
    Add a notification to the current transaction.
    The caller's normal database commit will save it.
    """

    if not user_id:
        return

    if not message:
        return

    session.add(
        Notification(
            user_id=user_id,
            message=message[:255],
            is_read=False,
        )
    )


# =========================================================
# GLOBAL NOTIFICATION CONTEXT
# =========================================================

@notifications_bp.app_context_processor
def inject_notifications():

    if not current_user.is_authenticated:

        return {
            "notification_items": [],
            "unread_notifications_count": 0,
        }

    notification_items = (
        Notification.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .limit(5)
        .all()
    )

    unread_count = (
        Notification.query
        .filter_by(
            user_id=current_user.id,
            is_read=False,
        )
        .count()
    )

    return {
        "notification_items": notification_items,
        "unread_notifications_count": unread_count,
    }


# =========================================================
# NOTIFICATIONS PAGE
# =========================================================

@notifications_bp.route("/")
@login_required
def index():

    notification_list = (
        Notification.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .all()
    )

    return render_template(
        "notifications/index.html",
        notifications=notification_list,
    )


# =========================================================
# MARK ONE NOTIFICATION AS READ
# =========================================================

@notifications_bp.route(
    "/<int:notification_id>/read",
    methods=["POST"],
)
@login_required
def mark_read(notification_id):

    notification = (
        Notification.query
        .filter_by(
            id=notification_id,
            user_id=current_user.id,
        )
        .first_or_404()
    )

    notification.is_read = True

    db.session.commit()

    return redirect(
        url_for(
            "notifications.index"
        )
    )


# =========================================================
# MARK ALL AS READ
# =========================================================

@notifications_bp.route(
    "/mark-all-read",
    methods=["POST"],
)
@login_required
def mark_all_read():

    (
        Notification.query
        .filter_by(
            user_id=current_user.id,
            is_read=False,
        )
        .update(
            {
                Notification.is_read: True,
            },
            synchronize_session=False,
        )
    )

    db.session.commit()

    return redirect(
        url_for(
            "notifications.index"
        )
    )


# =========================================================
# AUTOMATIC NOTIFICATION ENGINE
# =========================================================

@event.listens_for(
    Session,
    "after_flush",
)
def create_automatic_notifications(
    session,
    flush_context,
):
    """
    Automatically creates notifications when important
    records are created or their statuses change.

    No route needs to manually create notifications.
    """

    # Prevent duplicate notifications during repeated
    # flushes inside one transaction.
    notification_keys = session.info.setdefault(
        "notification_keys",
        set(),
    )

    def already_sent(key):

        if key in notification_keys:
            return True

        notification_keys.add(key)
        return False

    # =====================================================
    # NEW / CHANGED USERS
    # =====================================================

    for user in list(session.new) + list(session.dirty):

        if not isinstance(user, User):
            continue

        if user in session.deleted:
            continue

        try:

            state = inspect(user)

        except Exception:

            continue

        # -------------------------------------------------
        # NEW ACCOUNT
        # -------------------------------------------------

        if user in session.new:

            if user.role != User.ROLE_ADMIN:

                admins = (
                    session.query(User)
                    .filter(
                        User.role == User.ROLE_ADMIN,
                        User.is_active_account == True,
                    )
                    .all()
                )

                for admin in admins:

                    key = (
                        "new-user",
                        user.id,
                        admin.id,
                    )

                    if already_sent(key):
                        continue

                    add_notification(
                        session,
                        admin.id,
                        (
                            f"New {user.role} account "
                            f"registered: {user.full_name}. "
                            f"Please review the account approval."
                        ),
                    )

        # -------------------------------------------------
        # APPROVAL STATUS CHANGED
        # -------------------------------------------------

        if user in session.dirty:

            try:

                history = (
                    state.attrs.approval_status.history
                )

            except Exception:

                history = None

            if history and history.has_changes():

                new_status = user.approval_status

                key = (
                    "approval",
                    user.id,
                    new_status,
                )

                if not already_sent(key):

                    if new_status == User.APPROVAL_APPROVED:

                        add_notification(
                            session,
                            user.id,
                            (
                                "Your account has been approved "
                                "by the administrator. "
                                "You may now use the system."
                            ),
                        )

                    elif new_status == User.APPROVAL_REJECTED:

                        add_notification(
                            session,
                            user.id,
                            (
                                "Your account registration "
                                "has been rejected by the administrator."
                            ),
                        )

    # =====================================================
    # STUDENT ADVISER ASSIGNMENT
    # =====================================================

    for profile in list(session.dirty):

        if not isinstance(
            profile,
            StudentProfile,
        ):

            continue

        if profile in session.deleted:
            continue

        try:

            state = inspect(profile)

            history = (
                state.attrs.adviser_id.history
            )

        except Exception:

            continue

        if not history or not history.has_changes():
            continue

        adviser = profile.adviser

        if adviser:

            # Student notification
            key_student = (
                "adviser-assignment-student",
                profile.id,
                adviser.id,
            )

            if not already_sent(key_student):

                add_notification(
                    session,
                    profile.user.id,
                    (
                        f"An OJT Adviser has been assigned "
                        f"to you: {adviser.full_name}."
                    ),
                )

            # Adviser notification
            key_adviser = (
                "adviser-assignment-adviser",
                profile.id,
                adviser.id,
            )

            if not already_sent(key_adviser):

                add_notification(
                    session,
                    adviser.id,
                    (
                        f"Student {profile.user.full_name} "
                        f"has been assigned to you for OJT monitoring."
                    ),
                )

    # =====================================================
    # INTERNSHIP APPLICATIONS
    # =====================================================

    for application in list(session.new):

        if not isinstance(
            application,
            InternshipApplication,
        ):

            continue

        student = application.student
        company = application.company

        if not student or not company:
            continue

        # -------------------------------------------------
        # NEW APPLICATION -> PARTNER
        # -------------------------------------------------

        if company.user_id:

            key = (
                "new-application",
                application.id,
                company.user_id,
            )

            if not already_sent(key):

                add_notification(
                    session,
                    company.user_id,
                    (
                        f"New internship application received "
                        f"from {student.user.full_name} "
                        f"for {company.company_name}."
                    ),
                )

    # =====================================================
    # APPLICATION STATUS CHANGES
    # =====================================================

    for application in list(session.dirty):

        if not isinstance(
            application,
            InternshipApplication,
        ):

            continue

        try:

            state = inspect(application)

            history = (
                state.attrs.status.history
            )

        except Exception:

            continue

        if not history or not history.has_changes():
            continue

        student = application.student
        company = application.company

        if not student or not student.user:
            continue

        new_status = application.status

        key = (
            "application-status",
            application.id,
            new_status,
        )

        if already_sent(key):
            continue

        if new_status == (
            InternshipApplication.STATUS_ACCEPTED
        ):

            add_notification(
                session,
                student.user.id,
                (
                    f"Your application to "
                    f"{company.company_name} "
                    f"has been accepted."
                ),
            )

        elif new_status == (
            InternshipApplication.STATUS_REJECTED
        ):

            add_notification(
                session,
                student.user.id,
                (
                    f"Your application to "
                    f"{company.company_name} "
                    f"has been rejected."
                ),
            )

    # =====================================================
    # NEW INTERNSHIP
    # =====================================================

    for internship in list(session.new):

        if not isinstance(
            internship,
            Internship,
        ):

            continue

        student = internship.student

        if not student or not student.user:
            continue

        # Student notification
        key_student = (
            "new-internship-student",
            internship.id,
            student.user.id,
        )

        if not already_sent(key_student):

            add_notification(
                session,
                student.user.id,
                (
                    f"Your OJT placement with "
                    f"{internship.company.company_name} "
                    f"has been created successfully."
                ),
            )

        # Adviser notification if already assigned
        if student.adviser_id:

            key_adviser = (
                "new-internship-adviser",
                internship.id,
                student.adviser_id,
            )

            if not already_sent(key_adviser):

                add_notification(
                    session,
                    student.adviser_id,
                    (
                        f"A new OJT internship has been created "
                        f"for student {student.user.full_name}."
                    ),
                )

    # =====================================================
    # WEEKLY REPORTS
    # =====================================================

    for report in list(session.new):

        if not isinstance(
            report,
            WeeklyReport,
        ):

            continue

        internship = report.internship

        if not internship:
            continue

        student = internship.student

        if not student:
            continue

        # Adviser notification
        if student.adviser_id:

            key_adviser = (
                "new-weekly-report",
                report.id,
                student.adviser_id,
            )

            if not already_sent(key_adviser):

                add_notification(
                    session,
                    student.adviser_id,
                    (
                        f"Student {student.user.full_name} "
                        f"submitted Week {report.week_number} "
                        f"weekly report for review."
                    ),
                )

    # =====================================================
    # WEEKLY REPORT STATUS
    # =====================================================

    for report in list(session.dirty):

        if not isinstance(
            report,
            WeeklyReport,
        ):

            continue

        try:

            state = inspect(report)

            history = (
                state.attrs.status.history
            )

        except Exception:

            continue

        if not history or not history.has_changes():
            continue

        internship = report.internship

        if not internship:
            continue

        student = internship.student

        if not student or not student.user:
            continue

        new_status = report.status

        key = (
            "weekly-report-status",
            report.id,
            new_status,
        )

        if already_sent(key):
            continue

        if new_status == WeeklyReport.STATUS_APPROVED:

            add_notification(
                session,
                student.user.id,
                (
                    f"Your Week {report.week_number} "
                    f"weekly report has been approved."
                ),
            )

        elif new_status == WeeklyReport.STATUS_PENDING:

            add_notification(
                session,
                student.user.id,
                (
                    f"Your Week {report.week_number} "
                    f"weekly report was returned for correction."
                ),
            )

    # =====================================================
    # NARRATIVE REPORTS
    # =====================================================

    for report in list(session.new):

        if not isinstance(
            report,
            NarrativeReport,
        ):

            continue

        internship = report.internship

        if not internship:
            continue

        student = internship.student

        if not student:
            continue

        if student.adviser_id:

            key = (
                "new-narrative-report",
                report.id,
                student.adviser_id,
            )

            if not already_sent(key):

                add_notification(
                    session,
                    student.adviser_id,
                    (
                        f"Student {student.user.full_name} "
                        f"submitted a narrative report: "
                        f"{report.title}."
                    ),
                )

    # =====================================================
    # NARRATIVE REPORT STATUS
    # =====================================================

    for report in list(session.dirty):

        if not isinstance(
            report,
            NarrativeReport,
        ):

            continue

        try:

            state = inspect(report)

            history = (
                state.attrs.status.history
            )

        except Exception:

            continue

        if not history or not history.has_changes():
            continue

        internship = report.internship

        if not internship:
            continue

        student = internship.student

        if not student or not student.user:
            continue

        new_status = report.status

        key = (
            "narrative-status",
            report.id,
            new_status,
        )

        if already_sent(key):
            continue

        if new_status == "Approved":

            add_notification(
                session,
                student.user.id,
                (
                    f"Your narrative report "
                    f"'{report.title}' has been approved."
                ),
            )

        elif new_status == "Rejected":

            add_notification(
                session,
                student.user.id,
                (
                    f"Your narrative report "
                    f"'{report.title}' has been rejected."
                ),
            )

    # =====================================================
    # EVALUATIONS
    # =====================================================

    for evaluation in list(session.new):

        if not isinstance(
            evaluation,
            Evaluation,
        ):

            continue

        internship = evaluation.internship

        if not internship:
            continue

        student = internship.student

        if not student or not student.user:
            continue

        if evaluation.status == "Submitted":

            key = (
                "new-evaluation",
                evaluation.id,
                student.user.id,
            )

            if not already_sent(key):

                add_notification(
                    session,
                    student.user.id,
                    (
                        f"A {evaluation.evaluator_role or 'user'} "
                        f"evaluation has been submitted "
                        f"for your internship."
                    ),
                )

    # =====================================================
    # EVALUATION STATUS CHANGES
    # =====================================================

    for evaluation in list(session.dirty):

        if not isinstance(
            evaluation,
            Evaluation,
        ):

            continue

        try:

            state = inspect(evaluation)

            status_history = (
                state.attrs.status.history
            )

        except Exception:

            continue

        if (
            not status_history
            or not status_history.has_changes()
        ):

            continue

        internship = evaluation.internship

        if not internship:
            continue

        student = internship.student

        if not student or not student.user:
            continue

        if evaluation.status != "Submitted":
            continue

        key = (
            "evaluation-status",
            evaluation.id,
            student.user.id,
        )

        if already_sent(key):
            continue

        add_notification(
            session,
            student.user.id,
            (
                f"Your {evaluation.evaluator_role or 'user'} "
                f"evaluation has been submitted."
            ),
        )

    # =====================================================
    # CERTIFICATE UPLOAD
    # =====================================================

    for certificate in list(session.new):

        if not isinstance(
            certificate,
            Certificate,
        ):

            continue

        if not certificate.pdf_path:
            continue

        internship = certificate.internship

        if not internship:
            continue

        student = internship.student

        if not student or not student.user:
            continue

        key = (
            "certificate-upload",
            certificate.id,
            student.user.id,
        )

        if already_sent(key):

            continue

        add_notification(
            session,
            student.user.id,
            (
                "Your completed OJT certificate "
                "has been uploaded and is now available."
            ),
        )

    # =====================================================
    # CERTIFICATE PATH CHANGED
    # =====================================================

    for certificate in list(session.dirty):

        if not isinstance(
            certificate,
            Certificate,
        ):

            continue

        try:

            state = inspect(certificate)

            history = (
                state.attrs.pdf_path.history
            )

        except Exception:

            continue

        if not history or not history.has_changes():
            continue

        if not certificate.pdf_path:
            continue

        internship = certificate.internship

        if not internship:
            continue

        student = internship.student

        if not student or not student.user:
            continue

        key = (
            "certificate-upload-changed",
            certificate.id,
            student.user.id,
        )

        if already_sent(key):
            continue

        add_notification(
            session,
            student.user.id,
            (
                "Your completed OJT certificate "
                "has been uploaded and is now available."
            ),
        )


# =========================================================
# CLEAR TRANSACTION NOTIFICATION CACHE
# =========================================================

@event.listens_for(
    Session,
    "after_commit",
)
def clear_notification_keys(
    session,
):
    session.info.pop(
        "notification_keys",
        None,
    )


@event.listens_for(
    Session,
    "after_rollback",
)
def clear_notification_keys_after_rollback(
    session,
):
    session.info.pop(
        "notification_keys",
        None,
    )