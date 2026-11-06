import os
import re
import smtplib
import uuid

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
    IndustryPartner,
)


# =========================================================
# AUTH BLUEPRINT
# =========================================================

auth_bp = Blueprint("auth", __name__)


# =========================================================
# CMU DEPARTMENTS AND PROGRAMS
# =========================================================

CMU_DEPARTMENTS = {
    "CCS": ["BSIT"],
    "CTE": [
        "BEED",
        "BSE Major in English",
        "BSE Major in Mathematics",
        "BSE Major in Social Studies",
        "BECED",
    ],
    "CAS": [
        "BAJ",
        "BAPS",
        "BPA",
        "BSSW",
    ],
    "CCJE": [
        "BS Crim",
    ],
    "CBA": [
        "BSBA Major in FM",
        "BSBA Major in HRM",
        "BSBA Major in MM",
    ],
    "COA": [
        "BSMA",
        "BSA",
    ],
}


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
        return serializer.loads(
            token,
            salt="password-reset",
            max_age=1800
        )

    except (
        SignatureExpired,
        BadSignature,
    ):
        return None


# =========================================================
# PASSWORD RESET EMAIL
# =========================================================

def _send_reset_email(email, reset_url):
    mail_server = os.environ.get("MAIL_SERVER")
    mail_port = os.environ.get("MAIL_PORT")
    mail_username = os.environ.get("MAIL_USERNAME")
    mail_password = os.environ.get("MAIL_PASSWORD")

    mail_use_tls = (
        os.environ.get("MAIL_USE_TLS", "true").lower()
        == "true"
    )

    missing_settings = []

    if not mail_server:
        missing_settings.append("MAIL_SERVER")

    if not mail_port:
        missing_settings.append("MAIL_PORT")

    if not mail_username:
        missing_settings.append("MAIL_USERNAME")

    if not mail_password:
        missing_settings.append("MAIL_PASSWORD")

    if missing_settings:
        current_app.logger.error(
            "Password reset email is not configured. Missing: %s",
            ", ".join(missing_settings)
        )
        return False

    try:
        message = EmailMessage()

        message["Subject"] = (
            "CMU Internship Management System - Password Reset"
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

        port = int(mail_port)

        if mail_use_tls:
            with smtplib.SMTP(mail_server, port) as server:
                server.starttls()
                server.login(mail_username, mail_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(mail_server, port) as server:
                server.login(mail_username, mail_password)
                server.send_message(message)

        return True

    except Exception:
        current_app.logger.exception(
            "Password reset email failed."
        )
        return False


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard_redirect")
        )

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        remember = (
            request.form.get("remember") == "on"
        )

        if not email or not password:
            flash(
                "Please enter your email and password.",
                "danger"
            )
            return render_template(
                "auth/login.html",
                email=email
            )

        user = (
            User.query
            .filter_by(email=email)
            .first()
        )

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

        if user.role == User.ROLE_ADMIN:
            login_user(user, remember=remember)

            welcome_name = (
                user.first_name or "Administrator"
            )

            flash(
                f"Welcome back, {welcome_name}!",
                "success"
            )

            return redirect(
                url_for("main.dashboard_redirect")
            )

        if user.approval_status == User.APPROVAL_PENDING:
            flash(
                "Your account is still pending administrator approval.",
                "warning"
            )
            return render_template(
                "auth/login.html",
                email=email
            )

        if user.approval_status == User.APPROVAL_REJECTED:
            flash(
                "Your account has been rejected by the administrator.",
                "danger"
            )
            return render_template(
                "auth/login.html",
                email=email
            )

        if not user.is_active_account:
            flash(
                "Your account is currently inactive.",
                "danger"
            )
            return render_template(
                "auth/login.html",
                email=email
            )

        login_user(user, remember=remember)

        if user.role == User.ROLE_PARTNER:
            partner_profile = (
                IndustryPartner.query
                .filter_by(user_id=user.id)
                .first()
            )

            welcome_name = (
                partner_profile.company_name
                if partner_profile
                else "Industry Partner"
            )
        else:
            welcome_name = user.first_name or "User"

        flash(
            f"Welcome back, {welcome_name}!",
            "success"
        )

        return redirect(
            url_for("main.dashboard_redirect")
        )

    return render_template("auth/login.html")


# =========================================================
# REGISTER
# =========================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard_redirect")
        )

    form = {
        "role": "student",
        "full_name": "",
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "student_id": "",
        "student_id_number": "",
        "department": "",
        "program": "",
        "course": "",
        "year_level": "4th Year",
        "email": "",
        "contact_number": "",
        "company_name": "",
    }

    if request.method == "GET":
        return render_template(
            "auth/register.html",
            form=form
        )

    # -----------------------------------------------------
    # GET FORM VALUES
    # -----------------------------------------------------

    role = (
        request.form.get("role", "student")
        .strip()
        .lower()
    )

    first_name = request.form.get(
        "first_name", ""
    ).strip()

    middle_name = request.form.get(
        "middle_name", ""
    ).strip()

    last_name = request.form.get(
        "last_name", ""
    ).strip()

    full_name = request.form.get(
        "full_name", ""
    ).strip()

    student_id_number = request.form.get(
        "student_id_number", ""
    ).strip()

    legacy_student_id = request.form.get(
        "student_id", ""
    ).strip()

    if not student_id_number:
        student_id_number = legacy_student_id

    department = request.form.get(
        "department", ""
    ).strip()

    course = request.form.get(
        "course", ""
    ).strip()

    legacy_program = request.form.get(
        "program", ""
    ).strip()

    if not course:
        course = legacy_program

    year_level = request.form.get(
        "year_level", ""
    ).strip()

    email = (
        request.form.get("email", "")
        .strip()
        .lower()
    )

    contact_number = request.form.get(
        "contact_number", ""
    ).strip()

    password = request.form.get(
        "password", ""
    )

    confirm_password = request.form.get(
        "confirm_password", ""
    )

    company_name = request.form.get(
        "company_name", ""
    ).strip()

    # Supports the visible partner company field.
    partner_company_name = request.form.get(
        "partner_company_name", ""
    ).strip()

    if not company_name:
        company_name = partner_company_name

    verification_document = request.files.get(
        "verification_document"
    )

    # -----------------------------------------------------
    # BUILD STUDENT FULL NAME
    # -----------------------------------------------------

    if role == User.ROLE_STUDENT:
        if not full_name:
            full_name = " ".join(
                part
                for part in [
                    first_name,
                    middle_name,
                    last_name
                ]
                if part
            ).strip()

    elif role == User.ROLE_PARTNER:
        first_name = ""
        middle_name = ""
        last_name = ""
        full_name = ""

    # -----------------------------------------------------
    # PRESERVE FORM DATA
    # -----------------------------------------------------

    form = {
        "role": role,
        "full_name": full_name,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "student_id": student_id_number,
        "student_id_number": student_id_number,
        "department": department,
        "program": course,
        "course": course,
        "year_level": year_level or "4th Year",
        "email": email,
        "contact_number": contact_number,
        "company_name": company_name,
    }

    # -----------------------------------------------------
    # ROLE VALIDATION
    # -----------------------------------------------------

    if role not in {
        User.ROLE_STUDENT,
        User.ROLE_PARTNER
    }:
        flash(
            "Invalid registration role.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    # =====================================================
    # STUDENT NAME VALIDATION
    # =====================================================

    if role == User.ROLE_STUDENT:

        if not first_name or not last_name:

            if not full_name:
                flash(
                    "Please enter your first name and last name.",
                    "danger"
                )
                return render_template(
                    "auth/register.html",
                    form=form
                )

            name_parts = full_name.split()

            if len(name_parts) < 2:
                flash(
                    "Please enter your first name and last name.",
                    "danger"
                )
                return render_template(
                    "auth/register.html",
                    form=form
                )

            first_name = name_parts[0]
            last_name = name_parts[-1]

            if len(name_parts) > 2:
                middle_name = " ".join(
                    name_parts[1:-1]
                )

        name_pattern = (
            r"[A-Za-zÀ-ÖØ-öø-ÿ]+"
            r"(?: [A-Za-zÀ-ÖØ-öø-ÿ]+)*"
        )

        for label, value in [
            ("First Name", first_name),
            ("Middle Name", middle_name),
            ("Last Name", last_name)
        ]:
            if value and not re.fullmatch(
                name_pattern,
                value
            ):
                flash(
                    f"{label} must contain letters and spaces only.",
                    "danger"
                )
                return render_template(
                    "auth/register.html",
                    form=form
                )

        full_name = " ".join(
            part
            for part in [
                first_name,
                middle_name,
                last_name
            ]
            if part
        ).strip()

        form["full_name"] = full_name
        form["first_name"] = first_name
        form["middle_name"] = middle_name
        form["last_name"] = last_name

    # =====================================================
    # INDUSTRY PARTNER VALIDATION
    # =====================================================

    elif role == User.ROLE_PARTNER:

        if not company_name:
            flash(
                "Please enter your company name.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        form["company_name"] = company_name

    # -----------------------------------------------------
    # CONTACT NUMBER
    # -----------------------------------------------------

    if not contact_number:
        flash(
            "Please enter your contact number.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    if len(contact_number) > 20:
        flash(
            "Contact number must not exceed 20 characters.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    # -----------------------------------------------------
    # EMAIL
    # -----------------------------------------------------

    if not email:
        flash(
            "Please enter your email address.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    email_pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"

    if not re.fullmatch(email_pattern, email):
        flash(
            "Please enter a valid email address.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    # -----------------------------------------------------
    # PASSWORD
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

    if password != confirm_password:
        flash(
            "Passwords do not match.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    # =====================================================
    # ROLE-SPECIFIC REQUIRED FIELDS
    # =====================================================

    if role == User.ROLE_STUDENT:

        if department not in CMU_DEPARTMENTS:
            flash(
                "Please select a valid department.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        if course not in CMU_DEPARTMENTS[department]:
            flash(
                "Please select a valid program for your department.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        # Store department and program together in the
        # existing StudentProfile.course field.
        course = f"{department} - {course}"

        form["course"] = course
        form["program"] = course

        if year_level != "4th Year":
            flash(
                "Registration is limited to 4th-year students of City of Malabon University.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        if not student_id_number:
            flash(
                "Please enter your Student ID Number.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

    elif role == User.ROLE_PARTNER:

        if not company_name:
            flash(
                "Please enter your company name.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

    # =====================================================
    # VERIFICATION DOCUMENT
    # =====================================================

    if (
        verification_document is None
        or not verification_document.filename
    ):
        message = (
            "Please upload your Student ID."
            if role == User.ROLE_STUDENT
            else "Please upload your Business Permit."
        )

        flash(message, "danger")

        return render_template(
            "auth/register.html",
            form=form
        )

    original_filename = (
        verification_document.filename or ""
    )

    safe_original_filename = os.path.basename(
        original_filename
    ).strip()

    if not safe_original_filename:
        flash(
            "The selected verification document is invalid.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    extension = ""

    if "." in safe_original_filename:
        extension = (
            safe_original_filename.rsplit(".", 1)[1]
            .lower()
        )

    allowed_document_extensions = {
        "pdf",
        "jpg",
        "jpeg",
        "png"
    }

    if extension not in allowed_document_extensions:
        flash(
            "Invalid verification document. Please upload a PDF, JPG, JPEG, or PNG file.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    # -----------------------------------------------------
    # DUPLICATE EMAIL
    # -----------------------------------------------------

    existing_user = (
        User.query
        .filter(
            db.func.lower(User.email) == email
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
    # DUPLICATE STUDENT ID
    # -----------------------------------------------------

    if role == User.ROLE_STUDENT:

        existing_student = (
            StudentProfile.query
            .filter_by(
                student_id_number=student_id_number
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

    # =====================================================
    # PREPARE UPLOAD DIRECTORY
    # =====================================================

    upload_root = current_app.config.get(
        "UPLOAD_FOLDER"
    )

    if not upload_root:
        flash(
            "The upload folder is not configured.",
            "danger"
        )
        return render_template(
            "auth/register.html",
            form=form
        )

    if role == User.ROLE_STUDENT:
        verification_subfolder = "verification/student"
    else:
        verification_subfolder = "verification/partner"

    verification_folder = os.path.join(
        upload_root,
        verification_subfolder
    )

    try:
        os.makedirs(
            verification_folder,
            exist_ok=True
        )

    except OSError:
        current_app.logger.exception(
            "Could not create verification upload folder."
        )

        flash(
            "The verification document could not be saved. Please try again.",
            "danger"
        )

        return render_template(
            "auth/register.html",
            form=form
        )

    from werkzeug.utils import secure_filename

    base_name = secure_filename(
        os.path.splitext(
            safe_original_filename
        )[0]
    ) or "verification"

    unique_name = (
        f"{base_name}_{uuid.uuid4().hex}.{extension}"
    )

    verification_path = os.path.join(
        verification_folder,
        unique_name
    )

    relative_verification_path = os.path.join(
        verification_subfolder,
        unique_name
    ).replace("\\", "/")

    # =====================================================
    # CREATE ACCOUNT
    # =====================================================

    if role == User.ROLE_PARTNER:
        user_first_name = company_name
        user_middle_name = None
        user_last_name = ""
    else:
        user_first_name = first_name
        user_middle_name = middle_name or None
        user_last_name = last_name

    user = User(
        first_name=user_first_name,
        middle_name=user_middle_name,
        last_name=user_last_name,
        email=email,
        contact_number=contact_number,
        role=role,
        approval_status=User.APPROVAL_PENDING,
        is_active_account=False,
        verification_document_path=relative_verification_path,
        verification_document_type=(
            User.VERIFICATION_STUDENT_ID
            if role == User.ROLE_STUDENT
            else User.VERIFICATION_BUSINESS_PERMIT
        ),
        created_at=datetime.utcnow(),
    )

    user.set_password(password)

    try:
        verification_document.save(verification_path)

        db.session.add(user)
        db.session.flush()

        if role == User.ROLE_STUDENT:

            student_profile = StudentProfile(
                user_id=user.id,
                student_id_number=student_id_number,
                course=course,
                year_level="4th Year",
            )

            db.session.add(student_profile)

        elif role == User.ROLE_PARTNER:

            partner_profile = IndustryPartner(
                user_id=user.id,
                company_name=company_name,
                status="Active",
            )

            db.session.add(partner_profile)

        db.session.commit()

    except Exception:
        db.session.rollback()

        try:
            if os.path.exists(verification_path):
                os.remove(verification_path)

        except OSError:
            current_app.logger.exception(
                "Could not remove failed registration upload."
            )

        current_app.logger.exception(
            "Registration failed."
        )

        flash(
            "Registration could not be completed. Please check your information and try again.",
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
        "Registration successful. Your account is now pending administrator approval.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout")
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("main.landing")
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    current_app.logger.warning(
        "FORGOT PASSWORD ROUTE REACHED"
    )

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard_redirect")
        )

    dev_reset_url = None
    email = ""

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        if not email:
            flash(
                "Please enter your email address.",
                "danger"
            )

            return render_template(
                "auth/forgot_password_request.html",
                email=email,
                dev_reset_url=None
            )

        user = (
            User.query
            .filter_by(email=email)
            .first()
        )

        current_app.logger.warning(
            "FORGOT PASSWORD USER FOUND: %s",
            user is not None
        )

        if user:

            token = _generate_reset_token(user.email)

            reset_url = url_for(
                "auth.reset_password",
                token=token,
                _external=True
            )

            email_sent = _send_reset_email(
                user.email,
                reset_url
            )

            if not email_sent:
                dev_reset_url = reset_url

        flash(
            "If an account exists with that email, a password reset link has been generated.",
            "success"
        )

        return render_template(
            "auth/forgot_password_request.html",
            email=email,
            dev_reset_url=dev_reset_url
        )

    return render_template(
        "auth/forgot_password_request.html",
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

    email = _verify_reset_token(token)

    if email is None:
        flash(
            "This password reset link is invalid or has expired.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = (
        User.query
        .filter_by(email=email)
        .first()
    )

    if user is None:
        flash(
            "The account associated with this reset link could not be found.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password", ""
        )

        confirm_password = request.form.get(
            "confirm_password", ""
        )

        if len(password) < 6:
            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )

        if len(password) > 30:
            flash(
                "Password must not exceed 30 characters.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )

        user.set_password(password)

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

            flash(
                "The password could not be updated. Please try again.",
                "danger"
            )

            return render_template(
                "auth/reset_password.html",
                token=token
            )

        flash(
            "Your password has been reset successfully. You can now sign in using your new password.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        token=token
    )