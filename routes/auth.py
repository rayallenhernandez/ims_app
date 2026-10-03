import os
import re
import smtplib

from datetime import datetime

from email.message import EmailMessage

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)

from flask_login import (
    login_user,
    logout_user,
    current_user,
)

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired,
)

from extensions import db

from models import (
    User,
    StudentProfile,
)


# =========================================================
# AUTH BLUEPRINT
# =========================================================

auth_bp = Blueprint(
    "auth",
    __name__
)


# =========================================================
# PASSWORD RESET TOKEN HELPERS
# =========================================================

def _get_serializer():

    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )


def _generate_reset_token(email):

    serializer = _get_serializer()

    return serializer.dumps(
        email,
        salt="password-reset"
    )


def _verify_reset_token(token):

    serializer = _get_serializer()

    try:

        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=1800
        )

        return email

    except (
        SignatureExpired,
        BadSignature,
    ):

        return None


# =========================================================
# PASSWORD RESET EMAIL
# =========================================================

def _send_reset_email(
    email,
    reset_url
):

    """
    Sends the reset email when SMTP settings are configured.

    Returns:
        True  = email sent
        False = email not configured or sending failed
    """

    mail_server = os.environ.get(
        "MAIL_SERVER"
    )

    mail_port = os.environ.get(
        "MAIL_PORT"
    )

    mail_username = os.environ.get(
        "MAIL_USERNAME"
    )

    mail_password = os.environ.get(
        "MAIL_PASSWORD"
    )

    mail_use_tls = os.environ.get(
        "MAIL_USE_TLS",
        "true"
    ).lower() == "true"


    # -----------------------------------------------------
    # SMTP NOT CONFIGURED
    # -----------------------------------------------------

    if not all([
        mail_server,
        mail_port,
        mail_username,
        mail_password,
    ]):

        return False


    try:

        message = EmailMessage()

        message["Subject"] = (
            "CMU Internship Management System - "
            "Password Reset"
        )

        message["From"] = mail_username

        message["To"] = email


        message.set_content(
            f"""
Hello,

We received a request to reset your password
for the City of Malabon University Internship
Management System.

Click the link below to create a new password:

{reset_url}

This link will expire in 30 minutes.

If you did not request a password reset,
you can safely ignore this email.

City of Malabon University
Internship Management System
""".strip()
        )


        port = int(
            mail_port
        )


        # -------------------------------------------------
        # TLS
        # -------------------------------------------------

        if mail_use_tls:

            with smtplib.SMTP(
                mail_server,
                port
            ) as server:

                server.starttls()

                server.login(
                    mail_username,
                    mail_password
                )

                server.send_message(
                    message
                )


        # -------------------------------------------------
        # NO TLS
        # -------------------------------------------------

        else:

            with smtplib.SMTP(
                mail_server,
                port
            ) as server:

                server.login(
                    mail_username,
                    mail_password
                )

                server.send_message(
                    message
                )


        return True


    except Exception:

        return False


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # -----------------------------------------------------
    # ALREADY LOGGED IN
    # -----------------------------------------------------

    if current_user.is_authenticated:

        return redirect(
            url_for(
                "main.dashboard_redirect"
            )
        )


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        remember = (
            request.form.get(
                "remember"
            )
            == "on"
        )


        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not email or not password:

            flash(
                "Please enter your email and password.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                email=email
            )


        # -------------------------------------------------
        # FIND USER
        # -------------------------------------------------

        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )


        # -------------------------------------------------
        # CHECK PASSWORD
        # -------------------------------------------------

        if (
            user is None
            or not user.check_password(password)
        ):

            flash(
                "Incorrect email or password.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                email=email
            )


        # -------------------------------------------------
        # ADMIN ACCOUNTS
        # -------------------------------------------------

        if user.role == User.ROLE_ADMIN:

            login_user(
                user,
                remember=remember
            )

            flash(
                f"Welcome back, {user.first_name}!",
                "success"
            )

            return redirect(
                url_for(
                    "main.dashboard_redirect"
                )
            )


        # -------------------------------------------------
        # APPROVAL STATUS
        # -------------------------------------------------

        if user.approval_status == (
            User.APPROVAL_PENDING
        ):

            flash(
                "Your account is still pending administrator approval.",
                "warning"
            )

            return render_template(
                "auth/login.html",
                email=email
            )


        if user.approval_status == (
            User.APPROVAL_REJECTED
        ):

            flash(
                "Your account has been rejected by the administrator.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                email=email
            )


        # -------------------------------------------------
        # ACTIVE ACCOUNT
        # -------------------------------------------------

        if not user.is_active_account:

            flash(
                "Your account is currently inactive.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                email=email
            )


        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        login_user(
            user,
            remember=remember
        )

        flash(
            f"Welcome back, {user.first_name}!",
            "success"
        )

        return redirect(
            url_for(
                "main.dashboard_redirect"
            )
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "auth/login.html"
    )


# =========================================================
# REGISTER
# =========================================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # -----------------------------------------------------
    # ALREADY LOGGED IN
    # -----------------------------------------------------

    if current_user.is_authenticated:

        return redirect(
            url_for(
                "main.dashboard_redirect"
            )
        )


    # -----------------------------------------------------
    # DEFAULT FORM VALUES
    # -----------------------------------------------------

    form = {
        "full_name": "",
        "student_id": "",
        "program": "",
        "year_level": "4th Year",
        "email": "",
    }


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "auth/register.html",
            form=form
        )


    # =====================================================
    # POST
    # =====================================================

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    student_id = request.form.get(
        "student_id",
        ""
    ).strip()

    program = request.form.get(
        "program",
        ""
    ).strip()

    year_level = request.form.get(
        "year_level",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # -----------------------------------------------------
    # PRESERVE FORM DATA
    # -----------------------------------------------------

    form = {
        "full_name": full_name,
        "student_id": student_id,
        "program": program,
        "year_level": year_level,
        "email": email,
    }


    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    if not full_name:

        flash(
            "Please enter your full name.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    if not student_id:

        flash(
            "Please enter your Student ID.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    if not program:

        flash(
            "Please enter your program.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    if not email:

        flash(
            "Please enter your email address.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # YEAR LEVEL
    # -----------------------------------------------------

    if year_level != "4th Year":

        flash(
            "Registration is limited to 4th-year students of City of Malabon University.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # FULL NAME VALIDATION
    # -----------------------------------------------------

    if not re.fullmatch(
        r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?: [A-Za-zÀ-ÖØ-öø-ÿ]+)*",
        full_name
    ):

        flash(
            "Full Name must contain letters and spaces only.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # PASSWORD LENGTH
    # -----------------------------------------------------

    if len(password) < 6:

        flash(
            "Password must contain at least 6 characters.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    if len(password) > 30:

        flash(
            "Password must not exceed 30 characters.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # PASSWORD MATCH
    # -----------------------------------------------------

    if password != confirm_password:

        flash(
            "Passwords do not match.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # EMAIL CHECK
    # -----------------------------------------------------

    existing_user = (
        User.query
        .filter_by(
            email=email
        )
        .first()
    )

    if existing_user:

        flash(
            "An account with that email address already exists.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # STUDENT ID CHECK
    # -----------------------------------------------------

    existing_student = (
        StudentProfile.query
        .filter_by(
            student_id_number=student_id
        )
        .first()
    )

    if existing_student:

        flash(
            "That Student ID is already registered.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # SPLIT NAME
    # -----------------------------------------------------

    name_parts = full_name.split()

    first_name = name_parts[0]

    last_name = name_parts[-1]

    middle_name = None

    if len(name_parts) > 2:

        middle_name = " ".join(
            name_parts[1:-1]
        )


    # -----------------------------------------------------
    # CREATE USER
    # -----------------------------------------------------

    user = User(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        email=email,
        role=User.ROLE_STUDENT,
        approval_status=User.APPROVAL_PENDING,
        is_active_account=False,
        created_at=datetime.utcnow(),
    )

    user.set_password(
        password
    )

    db.session.add(
        user
    )

    db.session.flush()


    # -----------------------------------------------------
    # CREATE STUDENT PROFILE
    # -----------------------------------------------------

    student_profile = StudentProfile(
        user_id=user.id,
        student_id_number=student_id,
        course=program,
        year_level="4th Year",
    )

    db.session.add(
        student_profile
    )


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Registration could not be completed. "
            "Please check your information and try again.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    flash(
        "Registration successful. "
        "Your account is now pending administrator approval.",
        "success"
    )

    return redirect(
        url_for(
            "auth.login"
        )
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route(
    "/logout"
)
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for(
            "main.landing"
        )
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    # -----------------------------------------------------
    # ALREADY LOGGED IN
    # -----------------------------------------------------

    if current_user.is_authenticated:

        return redirect(
            url_for(
                "main.dashboard_redirect"
            )
        )


    dev_reset_url = None

    email = ""


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not email:

            flash(
                "Please enter your email address.",
                "danger"
            )

            return render_template(
                "auth/forgot_password.html",
                email=email,
                dev_reset_url=None
            )


        # -------------------------------------------------
        # FIND USER
        # -------------------------------------------------

        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )


        # -------------------------------------------------
        # GENERATE TOKEN
        # -------------------------------------------------

        if user:

            token = _generate_reset_token(
                user.email
            )


            reset_url = url_for(
                "auth.reset_password",
                token=token,
                _external=True
            )


            # ---------------------------------------------
            # TRY EMAIL
            # ---------------------------------------------

            email_sent = _send_reset_email(
                user.email,
                reset_url
            )


            # ---------------------------------------------
            # DEVELOPMENT FALLBACK
            # ---------------------------------------------

            if not email_sent:

                dev_reset_url = reset_url


        # -------------------------------------------------
        # GENERIC MESSAGE
        # -------------------------------------------------

        flash(
            "If an account exists with that email, "
            "a password reset link has been generated.",
            "success"
        )


        return render_template(
            "auth/forgot_password.html",
            email=email,
            dev_reset_url=dev_reset_url
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "auth/forgot_password.html",
        email=email,
        dev_reset_url=None
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    # -----------------------------------------------------
    # VERIFY TOKEN
    # -----------------------------------------------------

    email = _verify_reset_token(
        token
    )


    if email is None:

        flash(
            "This password reset link is invalid or has expired.",
            "danger"
        )

        return redirect(
            url_for(
                "auth.forgot_password"
            )
        )


    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    user = (
        User.query
        .filter_by(
            email=email
        )
        .first()
    )


    if user is None:

        flash(
            "The account associated with this reset link could not be found.",
            "danger"
        )

        return redirect(
            url_for(
                "auth.forgot_password"
            )
        )


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # -------------------------------------------------
        # MINIMUM LENGTH
        # -------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )


        # -------------------------------------------------
        # MAXIMUM LENGTH
        # -------------------------------------------------

        if len(password) > 30:

            flash(
                "Password must not exceed 30 characters.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )


        # -------------------------------------------------
        # PASSWORD MATCH
        # -------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )


        # -------------------------------------------------
        # SAVE NEW PASSWORD
        # -------------------------------------------------

        user.set_password(
            password
        )


        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "The password could not be updated. "
                "Please try again.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )


        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        flash(
            "Your password has been reset successfully. "
            "You can now sign in using your new password.",
            "success"
        )

        return redirect(
            url_for(
                "auth.login"
            )
        )


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "auth/reset_password.html",
        token=token
    )