import os
import api
from data.forms import *
from data import db_session
from data.__all_models import *
from sqlalchemy import or_, and_
from flask import Flask, render_template, redirect, request
from flask_login import login_user, logout_user, current_user, LoginManager, login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = "messenger"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return session.query(users.Users).get(user_id)


@app.errorhandler(401)
def unauthorized(error):
    return render_template('no_access.html'), 401


@app.errorhandler(404)
def error_handler(error):
    return render_template("error_handler.html", message="Страница не найдена."), 404


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title="ЯMessenger")


@app.route("/registration", methods=('GET', 'POST'))
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data == "" or form.login.data == "" or form.confirm_password.data == ""\
                or form.nickname.data == "":
            return render_template("registration.html", form=form, message="Заполните все поля")
        if form.password.data != form.confirm_password.data:
            return render_template("registration.html", form=form, message="Пароли не совпадают.")
        new_user = users.Users()
        new_user.name = form.nickname.data
        new_user.set_password(form.password.data)
        new_user.email = form.login.data
        session.add(new_user)
        session.commit()
        login_user(new_user)
        return redirect("/")
    return render_template("registration.html", form=form, message="")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/login", methods=('GET', 'POST'))
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.password.data == "" or form.login.data == "":
            return render_template("login.html", form=form, message="Заполните все поля")
        user = session.query(users.Users).filter(users.Users.email == form.login.data).first()
        if user is None:
            return render_template("login.html", form=form, message="Пользователь не найден")
        if not user.check_password(form.password.data):
            return render_template("login.html", form=form, message="Неправильный пароль")
        login_user(user, remember=form.remember.data)
        return redirect("/friends")
    return render_template("login.html", form=form, message="")


@app.route("/friends")
@login_required
def friend():
    friends_list = session.query(friends.Friends).filter(
        or_(friends.Friends.id_first_user == current_user.id,
            friends.Friends.id_second_user == current_user.id)).all()
    friends_list = [pair.id_first_user if pair.id_first_user != current_user.id
                    else pair.id_second_user for pair in friends_list]
    friends_list = [session.query(users.Users).get(user) for user in friends_list]
    invitations_list = session.query(friends_invitations.FriendsInv).filter(friends_invitations.FriendsInv.id_second_user == current_user.id).all()
    invitations = []
    for invitation in invitations_list:
        friend_id = invitation.id_first_user if invitation.id_first_user != current_user.id else invitation.id_second_user
        friend_name = session.query(users.Users).get(friend_id).name
        invitations += [{"id": invitation.id, "name": friend_name}]
    if len(invitations) == 0:
        invitations = False
    return render_template("friends.html", friends_list=friends_list, invitations_list=invitations)


@app.route("/user/<int:user_id>")
@login_required
def user_page(user_id):
    user = session.query(users.Users).get(user_id)
    if user is None:
        return render_template("error_handler.html", message="Пользователя с таким ID не существует")
    pair = session.query(friends.Friends).filter(
        or_(and_(friends.Friends.id_first_user == current_user.id, friends.Friends.id_second_user == user_id),
            and_(friends.Friends.id_first_user == user_id, friends.Friends.id_second_user == current_user.id))
    ).first()
    pair = False if pair is None else True
    invitation = session.query(friends_invitations.FriendsInv).filter(
        or_(and_(friends_invitations.FriendsInv.id_first_user == current_user.id,
                 friends_invitations.FriendsInv.id_second_user == user_id),
            and_(friends_invitations.FriendsInv.id_first_user == user_id,
                 friends_invitations.FriendsInv.id_second_user == current_user.id))).first()
    invitation = invitation if invitation is not None else False
    if invitation is not False:
        sender = True if invitation.id_first_user == current_user.id else False
    else:
        sender = False
    return render_template("user.html", user=user, pair=pair, invitation=invitation, sender=sender)


@app.route("/account")
@login_required
def account():
    pass  # TODO


@app.route("/add_friend/<int:user_id>")
@login_required
def add_friend(user_id):
    past = request.headers.environ["HTTP_REFERER"]
    new_friend_invitation = friends_invitations.FriendsInv()
    new_friend_invitation.id_first_user = current_user.id
    new_friend_invitation.id_second_user = user_id
    session.add(new_friend_invitation)
    session.commit()
    return redirect(past)


@app.route("/accept_friend/<int:invitation_id>")
@login_required
def accept_friend(invitation_id):
    try:
        past = request.headers.environ["HTTP_REFERER"]
    except KeyError:
        return render_template("error_handler.html", message="У вас недостаточно прав")
    invitation = session.query(friends_invitations.FriendsInv).get(invitation_id)
    if invitation is not None and invitation.id_first_user != current_user:
        new_friendship = friends.Friends()
        new_friendship.id_second_user = invitation.id_second_user
        new_friendship.id_first_user = invitation.id_first_user
        session.add(new_friendship)
        session.delete(invitation)
        session.commit()
    return redirect(past)


if __name__ == "__main__":
    db_session.global_init("db/database.sqlite")
    session = db_session.create_session()
    app.register_blueprint(api.api)
    #  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    app.run(host="127.0.0.1", port=8080)
