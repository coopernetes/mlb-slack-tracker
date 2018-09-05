from slack.token import Token
from slack.user import User
from flask import Flask, redirect, url_for, session, request, send_from_directory
from celery import Celery
import os

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = '7ce9431ef410e9fb730e140f290abd0b69e2568515b27644'
# app.config.update(
#     CELERY_BROKER_URL='redis://localhost:6379',
#     CELERY_RESULT_BACKEND='redis://localhost:6379'
# )
# celery = make_celery(app)

@app.route("/")
def hello():
    return app.send_static_file("slack_button.html")


@app.route("/authorize")
def authorize():
    try:
        t = Token(request.args.get('code'),
            request.args.get('redirect_uri'),
            os.environ['SLACK_CLIENT_ID'],
            os.environ['SLACK_CLIENT_SECRET'])
        session['token'] = t.generate_token()
        return redirect(url_for('successful'))
    except KeyError:
        return redirect(url_for('failed'))


@app.route("/success")
def successful():
    print("Token: {}".format(session['token']))
    user = User(token=session['token']['access_token'], id=session['token']['user_id'])
    return "Current user: {}\nStatus: {}\nEmoji: {}".format(user.id, user.display_status(), user.display_status_emot())


@app.route("/failure")
def failed():
    return "Authorization failed!"


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
