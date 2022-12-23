import sqlite3

import click
from flask import current_app, g
from . import logging

logger = logging.getLogger('db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def get_user(user_id):
    logger.debug('Getting user: user_id: %s', user_id)
    # fetch user, or None if not found
    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE user_id = ?', (user_id,)
    ).fetchone()
    logger.debug('User: %s', user)
    return user


def add_user(user_id, username):
    logger.info("Adding user: user_id: %s, username: %s", user_id, username)
    try:
        db = get_db()
        db.execute(
            'INSERT INTO user (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        db.commit()
    except db.IntegrityError:
        logger.error(
            "User is already registered: user_id: %s, username: %s",
            user_id, username)
        raise


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
