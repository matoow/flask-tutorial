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
from flaskr.db import *
from flask_awscognito import AWSCognitoAuthentication
import boto3
from botocore.config import Config
from flaskr.logging import getLogger
from urllib.parse import quote


cogauth = AWSCognitoAuthentication()
client = None
bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = getLogger('auth')

class EmailNotVerifiedError(Exception):
    pass


def init(app):
    global client
    global cogauth
    global sign_out_url

    sign_out_url = app.config.get('AWS_COGNITO_SIGN_OUT_URL')

    cogauth.init_app(app)

    #
    # access key ID and secret access key loaded via environment variables
    # or in ~/.aws/credentials
    #
    aws_config = Config(
        region_name=app.config.get('AWS_DEFAULT_REGION'),
        signature_version='v4',
    )
    client = boto3.client('cognito-idp', config=aws_config)

    app.before_request(before_request)


@bp.route('/login')
def login():
    return redirect(cogauth.get_sign_in_url())

def get_sign_out_url():
    global sign_out_url
    quoted_sign_out_url = quote(sign_out_url)

    full_url = (
        f"{cogauth.domain}/logout"
        f"?client_id={cogauth.user_pool_client_id}"
        f"&logout_uri={quoted_sign_out_url}"
    )
    return full_url

@bp.route('/logout')
def logout():
    session.clear()
    sign_out_url = get_sign_out_url()

    logger.info('signOutUrl: %s', sign_out_url)
    return redirect(sign_out_url)


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
        app_client_id=app.config.get('AWS_COGNITO_USER_POOL_CLIENT_ID'),
        testmode=True  # Disable token expiration check for testing purposes
    )


@bp.route('/callback')
def auth_callback():
    logger.info('auth_callback')

    access_token = cogauth.get_access_token(request.args)

    decoded = decode_token(access_token)
    user_id = decoded['sub']
    user = get_user(user_id)

    if user == None:
        register_user(access_token)
        user = get_user(user_id)

    g.user = user

    session['access_token'] = access_token
    resp = make_response(redirect(url_for("blog.index")))

    return resp


def before_request():
    #
    # call before each request
    #
    logger.info('before_request: %s', request.base_url)

    if request.base_url != url_for('auth.login'):
        access_token = session.get('access_token')

        if (access_token):
            decoded = decode_token(access_token)
            user_id = decoded['sub']

            user = get_user(user_id)

            if user == None:
                logger.info('user not found: %s', user_id)

            g.user = user
        else:
            g.user = None


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


def register_user(token):
    decoded = decode_token(token)
    user_id = decoded['sub']

    logger.info('registering user: user_id: %s', user_id)
    user_details = get_user_details(token)

    logger.info('userDetails: %s', user_details)

    if user_details['email_verified'] != 'true':
        #
        # this shouldn't be happening, as only verified users should be let
        # past the cognito login
        #
        raise EmailNotVerifiedError()

    username = user_details['email']
    add_user(user_id, username)


def get_user_details(token):
    res = client.get_user(AccessToken=token)

    attributes = dict([(r['Name'], r['Value']) for r in res['UserAttributes']])

    return attributes
