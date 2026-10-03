from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user


main_bp = Blueprint("main", __name__)


# =========================================================
# LANDING PAGE
# =========================================================

@main_bp.route("/")
def landing():
    """
    Public landing/login split page.
    If the user is already logged in, redirect them
    to the dashboard appropriate for their role.
    """

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard_redirect")
        )

    return render_template(
        "landing.html"
    )


# =========================================================
# DASHBOARD REDIRECT
# =========================================================

@main_bp.route("/dashboard")
def dashboard_redirect():
    """
    Redirect the logged-in user to the dashboard
    corresponding to their account role.
    """

    # -----------------------------------------------------
    # NOT LOGGED IN
    # -----------------------------------------------------

    if not current_user.is_authenticated:

        return redirect(
            url_for("main.landing")
        )


    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    if current_user.role == "student":

        return redirect(
            url_for("student.dashboard")
        )


    # -----------------------------------------------------
    # OJT ADVISER
    # -----------------------------------------------------

    elif current_user.role == "adviser":

        return redirect(
            url_for("adviser.dashboard")
        )


    # -----------------------------------------------------
    # INDUSTRY PARTNER
    # -----------------------------------------------------

    elif current_user.role == "partner":

        return redirect(
            url_for("partner.dashboard")
        )


    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    elif current_user.role == "admin":

        return redirect(
            url_for("admin.dashboard")
        )


    # -----------------------------------------------------
    # INVALID ROLE
    # -----------------------------------------------------

    else:

        return (
            "ERROR: Your account has an invalid role. "
            "Contact the administrator.",
            403
        )