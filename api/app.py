# This application serves as the main entry point for the Network Assessment API,
# setting up the Flask app and registering the necessary blueprints.

from flask import Flask
from routes.assessment import assessment_bp

app = Flask(__name__)


'''
Registering the blueprint for all the /assessment routes
Including /assessment/<ID> for accessing individual assessments by their ID and such
'''
app.register_blueprint(assessment_bp, url_prefix="/assessment")


if __name__ == "__main__":
    app.run(debug=True)
