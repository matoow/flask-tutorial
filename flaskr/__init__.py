import os
from flask import Flask

# moving to https://pypi.org/project/Flask-Cognito/

global cogauth

COGNITO_CONFIG = dict(
    COGNITO_REGION='ap-northeast-1',
    COGNITO_DOMAIN='localhost',
    COGNITO_USERPOOL_ID='ap-northeast-1_Yt2TJKlcN',
    COGNITO_APP_CLIENT_ID='4j2nh0nonrto9cadeic7m0phjn',
    # COGNITO_APP_CLIENT_SECRET='1ev8jmho7aacfd91l2ga4a44e5tml9e2emfdncabg2m614ujqhbp',
    COGNITO_REDIRECT_URL='http://localhost:5000/aws_cognito_redirect',
)


def create_app(test_config=None):
    global cogauth

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(dict(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        **COGNITO_CONFIG
    ))

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import aws_auth
    aws_auth.init(app)
    app.register_blueprint(aws_auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app
