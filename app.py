import os
from pathlib import Path

from flask import Flask

import db
from middleware import workspace


def create_app():
    """Create the Flask application and register its database commands."""
    app = Flask(__name__)
    app.config["DATABASE"] = Path(app.instance_path) / "techfest.sqlite3"
    project = Path(__file__).resolve().parent
    frontend = project / "frontend"
    if not frontend.is_dir():
        frontend = project.parent / "front end"
    app.config["TECHFEST_FRONTEND"] = frontend
    app.config["TECHFEST_TEAM_PASSWORD"] = os.environ.get("TECHFEST_TEAM_PASSWORD")
    db.init_app(app)
    app.register_blueprint(workspace)

    @app.get("/")
    def index():
        """Report database readiness without exposing stored records."""
        if not db.is_initialized():
            return {"status": "database not initialized"}, 503
        return {"status": "ready", "application": "CLE TechFest"}

    return app


app = create_app()
