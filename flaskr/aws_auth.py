import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from flask_cognito import CognitoAuth

cogauth = CognitoAuth()

def init(app):
    cogauth.init_app(app)

@cogauth.identity_handler
def lookup_cognito_user(payload):
    """Look up user in our database from Cognito JWT payload."""
    print(payload)
    # return User.query.filter(User.cognito_username == payload['username']).one_or_none()


bp = Blueprint('aws', __name__, url_prefix='/aws')

@bp.route('/login')
def login():
    return redirect(cogauth.get_sign_in_url())
