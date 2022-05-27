import os
import config
from views.poll import poll
from views.user import user
from secure.auth import auth
from flask import Flask, request, session, render_template


app = Flask(__name__)

app.secret_key = os.urandom(16)

auth.init_app(app)

app.register_blueprint(poll, url_prefix="/poll")
app.register_blueprint(user, url_prefix="/user")


@app.before_request
def require_auth():
    if request.endpoint in config.REQUIRE_AUTHENTICATION:
        if not auth.is_authenticated(session.get("token", "")):
            return "no"


@app.before_request
def no_auth():
    if request.endpoint in config.NO_AUTHENTICATION:
        if auth.is_authenticated(session.get("token", "")):
            return render_template("index.html")


if __name__ == "__main__":
    app.run()
