"""
Creates all tables and inserts demo data so you can log in and see every
screen populated, without needing real placements yet.

Usage:
    python seed.py
"""

from datetime import date

from app import create_app
from extensions import db
from models import (
    User,
    StudentProfile,
    IndustryPartner,
    Internship,
    WeeklyReport,
    NarrativeReport,
    Evaluation,
    Announcement,
)

app = create_app()

with app.app_context():

    # ---------------------------------------------------------
    # CREATE TABLES
    # ---------------------------------------------------------
    db.create_all()

    # ---------------------------------------------------------
    # CHECK IF DEMO DATA ALREADY EXISTS
    # ---------------------------------------------------------
    if User.query.filter_by(email="juan.delacruz@email.com").first():
        print("Demo student already exists.")

    else:

        # =====================================================
        # STUDENT
        # =====================================================
        student_user = User(
            first_name="Juan",
            last_name="Dela Cruz",
            email="juan.delacruz@email.com",
            contact_number="0917 123 4567",
            role=User.ROLE_STUDENT,
        )

        student_user.set_password("password123")
        db.session.add(student_user)
        db.session.flush()

        student_profile = StudentProfile(
            user_id=student_user.id,
            student_id_number="2023-00123",
            course="BS Information Technology",

            # Your system is now intended for 4th-year students.
            year_level="4th Year",

            section="BSIT-4A",
            school_year="2026 - 2027",
            address="City of Malabon University",
            skills="HTML, CSS, JavaScript, Python, Flask, MySQL, UI/UX Design",
            preferred_industries="Software Development, Web Development, IT Services / Consulting",
        )

        db.session.add(student_profile)

        # =====================================================
        # ADMINISTRATOR
        # =====================================================
        admin_user = User(
            first_name="Ana",
            last_name="Valdez",
            email="admin@ccs.edu",
            contact_number="0917 000 0000",
            role=User.ROLE_ADMIN,
        )

        admin_user.set_password("password123")
        db.session.add(admin_user)

        # =====================================================
        # OJT ADVISER
        # =====================================================
        adviser_user = User(
            first_name="Maria",
            middle_name="Santos",
            last_name="Garcia",
            email="adviser@ccs.edu",
            contact_number="0917 111 1111",
            role=User.ROLE_ADVISER,
        )

        adviser_user.set_password("password123")
        db.session.add(adviser_user)

        # =====================================================
        # INDUSTRY PARTNER
        # =====================================================
        partner_user = User(
            first_name="Carlo",
            last_name="Reyes",
            email="partner@techsolutions.com",
            contact_number="0917 555 1234",
            role=User.ROLE_PARTNER,
        )

        partner_user.set_password("password123")
        db.session.add(partner_user)
        db.session.flush()

        # =====================================================
        # COMPANY
        # =====================================================
        company = IndustryPartner(
            user_id=partner_user.id,
            company_name="TechSolutions Inc.",
            industry="Information Technology",
            available_slots=10,
            status="Active",
        )

        db.session.add(company)
        db.session.flush()

        # =====================================================
        # INTERNSHIP PLACEMENT
        # =====================================================
        internship = Internship(
            student_id=student_profile.id,
            company_id=company.id,
            department="Information Technology",
            supervisor_name="Engr. Maria Santos",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 7, 31),
            required_hours=240,
            completed_hours=120,
            status=Internship.STATUS_ACTIVE,
        )

        db.session.add(internship)
        db.session.flush()

        # =====================================================
        # WEEKLY REPORTS
        # =====================================================
        db.session.add(
            WeeklyReport(
                internship_id=internship.id,
                week_number=1,
                status="Approved",
            )
        )

        db.session.add(
            WeeklyReport(
                internship_id=internship.id,
                week_number=2,
                status="Pending",
            )
        )

        # =====================================================
        # NARRATIVE REPORT
        # =====================================================
        db.session.add(
            NarrativeReport(
                internship_id=internship.id,
                title="Mid-Term Narrative Report",
            )
        )

        # =====================================================
        # EVALUATION
        # =====================================================
        db.session.add(
            Evaluation(
                internship_id=internship.id,
                evaluator_name="Maria Santos",
                evaluator_role="Supervisor",
                score=4.5,
                status="Submitted",
            )
        )

        # =====================================================
        # ANNOUNCEMENTS
        # =====================================================
        db.session.add(
            Announcement(
                title="Mid-Term Evaluation schedule has been posted.",
                body="Please check the Evaluation section.",
                posted_by="OJT Office",
            )
        )

        db.session.add(
            Announcement(
                title="Weekly report for Week 5 is now available.",
                body="Submit your report before the deadline.",
                posted_by="OJT Office",
            )
        )

        # =====================================================
        # SAVE EVERYTHING
        # =====================================================
        db.session.commit()

        print()
        print("==============================================")
        print("       IMS DEMO DATA CREATED SUCCESSFULLY")
        print("==============================================")
        print()
        print("STUDENT")
        print("Email:    juan.delacruz@email.com")
        print("Password: password123")
        print()
        print("ADMINISTRATOR")
        print("Email:    admin@ccs.edu")
        print("Password: password123")
        print()
        print("OJT ADVISER")
        print("Email:    adviser@ccs.edu")
        print("Password: password123")
        print()
        print("INDUSTRY PARTNER")
        print("Email:    partner@techsolutions.com")
        print("Password: password123")
        print()
        print("==============================================")
        """Creates all tables and inserts demo data so you can log in and see every
screen populated, without needing real placements yet.

Usage:
    python seed.py
"""

from datetime import date

from app import create_app
from extensions import db
from models import (
    User,
    StudentProfile,
    IndustryPartner,
    Internship,
    WeeklyReport,
    NarrativeReport,
    Evaluation,
    Announcement,
)

app = create_app()

with app.app_context():

    # ---------------------------------------------------------
    # CREATE TABLES
    # ---------------------------------------------------------
    db.create_all()

    # ---------------------------------------------------------
    # CHECK IF DEMO DATA ALREADY EXISTS
    # ---------------------------------------------------------
    if User.query.filter_by(email="juan.delacruz@email.com").first():
        print("Demo student already exists.")

    else:

        # =====================================================
        # STUDENT
        # =====================================================
        student_user = User(
            first_name="Juan",
            last_name="Dela Cruz",
            email="juan.delacruz@email.com",
            contact_number="0917 123 4567",
            role=User.ROLE_STUDENT,
        )

        student_user.set_password("password123")
        db.session.add(student_user)
        db.session.flush()

        student_profile = StudentProfile(
            user_id=student_user.id,
            student_id_number="2023-00123",
            course="BS Information Technology",

            # Your system is now intended for 4th-year students.
            year_level="4th Year",

            section="BSIT-4A",
            school_year="2026 - 2027",
            address="City of Malabon University",
            skills="HTML, CSS, JavaScript, Python, Flask, MySQL, UI/UX Design",
            preferred_industries="Software Development, Web Development, IT Services / Consulting",
        )

        db.session.add(student_profile)

        # =====================================================
        # ADMINISTRATOR
        # =====================================================
        admin_user = User(
            first_name="Ana",
            last_name="Valdez",
            email="admin@ccs.edu",
            contact_number="0917 000 0000",
            role=User.ROLE_ADMIN,
        )

        admin_user.set_password("password123")
        db.session.add(admin_user)

        # =====================================================
        # OJT ADVISER
        # =====================================================
        adviser_user = User(
            first_name="Maria",
            middle_name="Santos",
            last_name="Garcia",
            email="adviser@ccs.edu",
            contact_number="0917 111 1111",
            role=User.ROLE_ADVISER,
        )

        adviser_user.set_password("password123")
        db.session.add(adviser_user)

        # =====================================================
        # INDUSTRY PARTNER
        # =====================================================
        partner_user = User(
            first_name="Carlo",
            last_name="Reyes",
            email="partner@techsolutions.com",
            contact_number="0917 555 1234",
            role=User.ROLE_PARTNER,
        )

        partner_user.set_password("password123")
        db.session.add(partner_user)
        db.session.flush()

        # =====================================================
        # COMPANY
        # =====================================================
        company = IndustryPartner(
            user_id=partner_user.id,
            company_name="TechSolutions Inc.",
            industry="Information Technology",
            available_slots=10,
            status="Active",
        )

        db.session.add(company)
        db.session.flush()

        # =====================================================
        # INTERNSHIP PLACEMENT
        # =====================================================
        internship = Internship(
            student_id=student_profile.id,
            company_id=company.id,
            department="Information Technology",
            supervisor_name="Engr. Maria Santos",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 7, 31),
            required_hours=240,
            completed_hours=120,
            status=Internship.STATUS_ACTIVE,
        )

        db.session.add(internship)
        db.session.flush()

        # =====================================================
        # WEEKLY REPORTS
        # =====================================================
        db.session.add(
            WeeklyReport(
                internship_id=internship.id,
                week_number=1,
                status="Approved",
            )
        )

        db.session.add(
            WeeklyReport(
                internship_id=internship.id,
                week_number=2,
                status="Pending",
            )
        )

        # =====================================================
        # NARRATIVE REPORT
        # =====================================================
        db.session.add(
            NarrativeReport(
                internship_id=internship.id,
                title="Mid-Term Narrative Report",
            )
        )

        # =====================================================
        # EVALUATION
        # =====================================================
        db.session.add(
            Evaluation(
                internship_id=internship.id,
                evaluator_name="Maria Santos",
                evaluator_role="Supervisor",
                score=4.5,
                status="Submitted",
            )
        )

        # =====================================================
        # ANNOUNCEMENTS
        # =====================================================
        db.session.add(
            Announcement(
                title="Mid-Term Evaluation schedule has been posted.",
                body="Please check the Evaluation section.",
                posted_by="OJT Office",
            )
        )

        db.session.add(
            Announcement(
                title="Weekly report for Week 5 is now available.",
                body="Submit your report before the deadline.",
                posted_by="OJT Office",
            )
        )

        # =====================================================
        # SAVE EVERYTHING
        # =====================================================
        db.session.commit()

        print()
        print("==============================================")
        print("       IMS DEMO DATA CREATED SUCCESSFULLY")
        print("==============================================")
        print()
        print("STUDENT")
        print("Email:    juan.delacruz@email.com")
        print("Password: password123")
        print()
        print("ADMINISTRATOR")
        print("Email:    admin@ccs.edu")
        print("Password: password123")
        print()
        print("OJT ADVISER")
        print("Email:    adviser@ccs.edu")
        print("Password: password123")
        print()
        print("INDUSTRY PARTNER")
        print("Email:    partner@techsolutions.com")
        print("Password: password123")
        print()
        print("==============================================")