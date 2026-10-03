from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():

    existing = User.query.filter_by(
        email="adviser@cmu.edu.ph"
    ).first()

    if existing:
        print("Adviser account already exists.")

    else:
        adviser = User(
            first_name="Maria",
            last_name="Santos",
            email="adviser@cmu.edu.ph",
            contact_number="0917 111 2222",
            role=User.ROLE_ADVISER,
        )

        adviser.set_password("password123")

        db.session.add(adviser)
        db.session.commit()

        print("Adviser account created successfully.")
        print("Adviser login: adviser@cmu.edu.ph / password123")