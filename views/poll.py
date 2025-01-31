import sse
import uuid
import controllers.user as user
import controllers.poll as controller
from secure.auth import auth
from .message import Message
from mongoengine import ValidationError
from flask import Blueprint, render_template, request, session, Response, abort, redirect, url_for

poll = Blueprint('poll', __name__, template_folder='templates')


@poll.route("/view")
def view_all():
    polls = controller.get_polls(author=auth.get_user(session).id)
    return render_template("overview.html", polls=polls)


@poll.route("/vote/<id>", methods=["GET", "POST"])
def vote(id):
    if not (pl := controller.get_poll(id=id)):
        abort(404)  # not found

    author = user.get_user(id=pl.author)

    if request.method == "POST":
        if auth.is_authenticated(session) and author:
            if author.id == auth.get_user(session).id:
                return render_template(
                    "vote.html",
                    poll=pl,
                    author=author.name if author else "Deleted User",
                    message=Message("error", "You must not vote on your own poll."))

        if len(request.form) != 1:
            return render_template(
                "vote.html",
                poll=pl,
                author=author.name if author else "Deleted User",
                message=Message("warning", "No option was selected."))

        choice = list(request.form)[0]

        for option in pl.options:
            if uuid.UUID(choice) == option.id:
                option.votes += 1
                pl.save()
                return render_template("index.html")

        return render_template(
            "vote.html",
            poll=pl,
            author=author.name if author else "Deleted User",
            message=Message("error", "Something went wrong selecting your option."))
    else:
        return render_template(
            "vote.html",
            poll=pl,
            author=author.name if author else "Deleted User")


@poll.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        options = []

        for field in request.form:
            if "option" in field:
                options.append(request.form[field])

        try:
            poll = controller.create_poll(
                auth.get_user(session).id,
                options,
                request.form.get("title"),
                request.form.get("desc"))

            if poll:
                return redirect(url_for("poll.view_all"))
            else:
                return render_template(
                    "signup.html",
                    message=Message("error", "Unknown error occurred while creating poll."))

        except ValidationError as e:
            return render_template("create.html", message=Message("warning", e))
    else:
        return render_template("create.html")


@poll.route("/delete/<id>")
def delete(id):
    if not (pl := controller.get_poll(id=id)):
        abort(404)  # not found

    if pl.author != auth.get_user(session).id:
        abort(401)  # unauthorised

    controller.delete_poll(pl.id)
    return redirect(url_for("poll.view_all"))


@poll.route("/listen", methods=["GET"])
def listen():

    def stream():
        messages = sse.announcer.listen()
        while True:
            msg = messages.get()
            yield msg

    return Response(stream(), mimetype="text/event-stream")
