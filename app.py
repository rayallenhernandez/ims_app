import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template
from config import config
from extensions import db, login_manager, migrate


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    from routes.partner import partner_bp
    from routes.main import main_bp
    from routes.adviser import adviser_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(partner_bp, url_prefix="/partner")
    app.register_blueprint(adviser_bp, url_prefix="/adviser")
    app.register_blueprint(
        notifications_bp,
        url_prefix="/notifications"
    )

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"now_year": datetime.utcnow().year}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)