
import click
from flask import current_app, g
from flaskr import logging

from psycopg import Connection
from flaskr.aws_secret import get_secret

logger = logging.getLogger('db')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def db_connect(config):
    conn_params = get_connection_params(config)
    logger.debug(
        'connecting to databse with: {username}@{host}/{db_name}'.format(**conn_params))
    return Connection.connect(fmt_connection_str(conn_params))


def get_connection_params(config):
    return get_secret(
        config.get('PG_AWS_SECRET'),
        config.get('PG_AWS_REGION')
    )


def fmt_connection_str(conn_params):
    return 'postgresql://{username}@{host}/{db_name}?password={password}'.format(**conn_params)


def get_db():
    if 'db' not in g:
        g.db = db_connect(current_app.config)

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('postgres_schema.sql') as f:
        sql = f.read().decode('utf8')
        logger.debug("sql: %s", sql)
        with db.cursor() as curs:
            curs.execute(sql)

        db.commit()

@ click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def get_user(user_id):
    logger.debug('Getting user: user_id: %s', user_id)

    with get_db().cursor() as curs:
        row = curs.execute(
            'SELECT * FROM tUser WHERE user_id = %s', (user_id,)
        ).fetchone()
        logger.debug('User: %s', row)

    return row


def add_user(user_id, username):
    logger.info("Adding tUser: user_id: %s, username: %s", user_id, username)
    try:
        conn = get_db()

        with conn.cursor() as curs:
            curs.execute(
                'INSERT INTO tUser (user_id, username) VALUES (%s, %s)',
                (user_id, username)
            )

        conn.commit()

    except:
        logger.error(
            "User is already registered: user_id: %s, username: %s",
            user_id, username)
        raise


def get_posts():
    with get_db().cursor() as curs:
        posts = curs.execute(
            'SELECT p.id, p.title, p.body, p.created, u.user_id, u.username'
            ' FROM tPost p JOIN tUser u ON p.user_id = u.user_id'
            ' ORDER BY created DESC'
        ).fetchall()

    return posts
