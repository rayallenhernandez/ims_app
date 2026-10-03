from app import create_app
from models import User, StudentProfile

app = create_app()

with app.app_context():

    adviser = User.query.filter_by(
        email="adviser@cmu.edu.ph"
    ).first()

    print("\n========== ADVISER ==========")

    if adviser:
        print("Name:", adviser.first_name, adviser.last_name)
        print("Email:", adviser.email)
        print("ID:", adviser.id)
        print("Role:", adviser.role)
    else:
        print("ADVISER ACCOUNT NOT FOUND")

    print("\n========== ASSIGNED STUDENTS ==========")

    if adviser:

        students = (
            StudentProfile.query
            .filter_by(adviser_id=adviser.id)
            .all()
        )

        print("Number of assigned students:", len(students))

        for student in students:

            print(
                "Student ID:",
                student.id,
                "| Student Number:",
                student.student_id_number,
                "| Name:",
                student.user.first_name,
                student.user.last_name,
                "| Adviser ID:",
                student.adviser_id
            )

    print("\n========================================\n")