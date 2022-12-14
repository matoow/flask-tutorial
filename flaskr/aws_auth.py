import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db


bp = Blueprint('aws', __name__, url_prefix='/aws')

@bp.route('/login')
def login():
    return redirect(g.cognito.get_sign_in_url())