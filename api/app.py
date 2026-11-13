# This application serves as the main entry point for the Network Assessment API,
# setting up the Flask app and registering the necessary blueprints.

import os

from flask import Flask
from dotenv import load_dotenv
from routes.assessment import assessment_bp
from routes.dashboard import dashboard_bp
from routes.targets import targets_bp



BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'frontend', 'static')
)


'''
Registering the blueprint for all the /assessment routes
Including /assessment/<ID> for accessing individual assessments by their ID and such
'''
app.register_blueprint(assessment_bp, url_prefix="/assessment")


app.register_blueprint(dashboard_bp, url_prefix="/dashboard")


app.register_blueprint(targets_bp, url_prefix="/api")


if __name__ == "__main__":
    app.run(debug=True)
