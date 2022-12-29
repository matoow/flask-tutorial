import sqlite3

import click
from flask import current_app, g
from flaskr import logging

from psycopg import Connection
from flaskr.aws_secret import get_secret

logger = logging.getLogger('db')

global PG_CONNECT_STRING


def init_app(app):
    global PG_CONNECT_STRING
    PG_CONNECT_STRING = get_connect_string(app.config)
    logger.info('PG_CONNECT_STRING: %s', PG_CONNECT_STRING)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def get_connect_string(config):
    secret = get_secret(
        config.get('PG_AWS_SECRET'),
        config.get('PG_AWS_REGION')
    )

    return 'postgresql://{user}@{host}/{db}?password={password}'.format(
        user=secret['username'],
        host=secret['host'],
        db=secret['dbInstanceIdentifier'],
        password=secret['password']
    )


def get_db():
    if 'db' not in g:
        # postgresql://[userspec@][hostspec][/dbname][?paramspec]
        g.db = Connection(PG_CONNECT_STRING)

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@ click.command('init-db')
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
