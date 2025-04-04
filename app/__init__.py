import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # ✅ إضافة
from .filters import insert_ad_after_paragraph


db = SQLAlchemy()
migrate = Migrate()  # ✅ إضافة


def create_app():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    static_folder = os.path.join(BASE_DIR, "static")
    template_folder = os.path.join(BASE_DIR, "app", "templates")

    app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
    app.jinja_env.filters["insert_ad"] = insert_ad_after_paragraph
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-dev-key")

    app.secret_key = "supersecretkey"

    db_path = os.path.join(BASE_DIR, "tecBamin.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.abspath(db_path)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)  # ✅ تفعيل Flask-Migrate

    from app.routes import main

    app.register_blueprint(main)

    from app.filters import to_egypt_time_str

    app.jinja_env.filters["to_egypt_time"] = to_egypt_time_str

    from datetime import datetime

    app.jinja_env.globals["current_year"] = datetime.now().year

    from flask import render_template

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("500.html"), 500

    return app
