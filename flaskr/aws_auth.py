from flask import (
    Blueprint, redirect, request, jsonify, make_response, url_for
)
from flask_jwt_extended import (
    JWTManager,
    set_access_cookies
)


from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from flask_awscognito import AWSCognitoAuthentication

cogauth = AWSCognitoAuthentication()
jwt = JWTManager()

bp = Blueprint('aws', __name__, url_prefix='/aws')

def init(app):
    cogauth.init_app(app)
    jwt = JWTManager(app)

@bp.route('/login')
def sign_in():
    return redirect(cogauth.get_sign_in_url())


@bp.route('/')
@cogauth.authentication_required
def index():
    claims = cogauth.claims  # also available through g.cognito_claims
    return jsonify({'claims': claims})


@bp.route('/authCallback')
def auth_callback():
    access_token = cogauth.get_access_token(request.args)
    resp = make_response(redirect(url_for("blog.index")))
    set_access_cookies(resp, access_token, max_age=30 * 60)
    return resp
