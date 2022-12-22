import functools
from flask import (
    Blueprint,
    redirect,
    request,
    jsonify,
    make_response,
    url_for,
    g,
    current_app,
    session
)
import cognitojwt
from flaskr.db import get_db
from flask_awscognito import AWSCognitoAuthentication
import boto3
from botocore.config import Config
from . import logging


cogauth = AWSCognitoAuthentication()
client = None
bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = logging.getLogger('auth')


def init(app):
    global client
    global cogauth

    cogauth.init_app(app)

    # access key ID and secret access key loaded via environment variables
    # or in ~/.aws/credentials
    aws_config = Config(
        region_name=app.config.get('AWS_DEFAULT_REGION'),
        signature_version='v4',
    )
    client = boto3.client('cognito-idp', config=aws_config)


@bp.route('/login')
def login():
    return redirect(cogauth.get_sign_in_url())


@bp.route('/logout')
def logout():
    session.clear()
    signOutUrl = cogauth.get_sign_in_url().replace('login', 'logout')
    return redirect(signOutUrl)

@bp.route('/')
@cogauth.authentication_required
def index():
    claims = cogauth.claims  # also available through g.cognito_claims
    return jsonify({'claims': claims})


def decode_token(id_token):
    app = current_app

    return cognitojwt.decode(
        id_token,
        app.config.get('AWS_DEFAULT_REGION'),
        app.config.get('AWS_COGNITO_USER_POOL_ID'),
        app_client_id=app.config.get(
            'AWS_COGNITO_USER_POOL_CLIENT_ID'),  # Optional
        testmode=True  # Disable token expiration check for testing purposes
    )


@bp.route('/callback')
def auth_callback():
    access_token = cogauth.get_access_token(request.args)
    logger.info('cogauth.claims: %s', cogauth.claims)
    logger.info('access_token: %s', access_token)

    session['access_token'] = access_token
    resp = make_response(redirect(url_for("blog.index")))

    return resp


@bp.before_app_request
def load_logged_in_user():
    logger.info('load_logged_in_user: %s', request.base_url)
    access_token = session.get('access_token')
    if (access_token):
        decoded = decode_token(access_token)
        user_id = decoded['sub']
        logger.info('user_id: %s', user_id)
        g.user_id = user_id
    else:
        g.user_id = None


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user_id is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def get_user_details(token):
    return client.get_user(AccessToken=token)
