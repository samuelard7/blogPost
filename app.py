from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
import smtplib
import pandas as pd
from random import randint
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, AdminLoginForm, AdminContactForm

count = 5
em_ail = None
unique_id = None

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBu88465nA6O6dondsdffgSihBXox7C0sKR6b'
my_email = "samuelrichard214@gmail.com"
password = "ebsv xtyp eeuc pufg"
ckeditor = CKEditor(app)
Bootstrap5(app)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_NF0wDWKkZLJ6@ep-super-shadow-a45g9gn4.us-east-1.aws.neon.tech/neondb?sslmode=require'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

class Contact(db.Model):
    __tablename__ = "contact"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)

class AdminContact(db.Model):
    __tablename__ = "adminqueries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(10))
    reply: Mapped[str] = mapped_column(Text)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

@login_manager.user_loader
def load_user(user_id):
    global unique_id
    global em_ail
    unique_id = user_id
    em_ail = db.session.execute(db.select(User.email).where(User.id==user_id)).scalar()
    return db.get_or_404(User, user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        new_user_contact_details = Contact(
            email=form.email.data,
            name=form.name.data,
            mobile='Nan',
            message='Nan',
        )
        db.session.add(new_user_contact_details)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, current_user=current_user)

@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    global count
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            flash("Incorrect Credentials, please try again.")
            return redirect(url_for('admin_login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("admin_login.html", form=form, current_user=current_user)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    global count
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user.email == 'samuelard715@outlook.com':
            flash('Please go to admin login tab to logged in as a admin..')
            return redirect(url_for('login'))
        if not user:
            flash("Email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            count = count - 1
            flash('Password incorrect, please try again.')
            if count == 0:
                flash('Account Blocked!!!')
                return redirect(url_for('login'))
            elif 0 < count < 3:
                flash(f'You {count} attempts left!!!')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)

@app.route("/contact-admin", methods=["GET", "POST"])
@admin_only
def admincontact():
    form = AdminContactForm()
    result = db.session.execute(db.select(Contact))
    query = [[c.name, c.email, c.mobile, c.message] for c in result.scalars()]
    columns = ["Name", "Email", "Mobile", "Message"]

    df = pd.DataFrame(query, columns=columns).to_html()
    Query_no = randint(1,9999)
    if form.validate_on_submit():
        email = form.email.data
        message = form.reply.data
    
        with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                connection.sendmail(from_addr=my_email, to_addrs=email,
                            msg=f"Subject:Refno: {Query_no} Thank you for contacting BlogFocus\n\n {message} \n\n\n Feel free to contact again. \n\n Richard Samuel \n Developer @BlogFocus ")
        flash('Successfully Sended.',category="success")
        delete_query = db.session.execute(db.select(Contact.id).where(Contact.email == email)).scalar()
        print(delete_query)
        if delete_query:
            query_to_delete = db.get_or_404(Contact, delete_query)
            db.session.delete(query_to_delete)
            db.session.commit()
        return redirect(url_for('admincontact'))
    return render_template("Admincontact.html",current_user=current_user ,form =form, query =df)

@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)

@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        if unique_id == None:
            flash('Please login in to contact..')
            return redirect(url_for('login'))
        result = db.session.execute(db.select(Contact).where(Contact.email == email))
        user = result.scalar()
        if user.id == 1:
            flash(f'Please check the email it should be {em_ail}. Try Again!')
            return redirect(url_for('contact',stored_text = em_ail))
        if user:
            user.message = message
            user.mobile = phone
            db.session.commit()
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                connection.sendmail(from_addr=email, to_addrs=my_email,
                            msg=f"Subject:{name} sends a message\n\n {message} \n\n\n Mob:{phone}")
            flash('Successfully Sended.',category="success")
            return redirect(url_for('contact'))
        else:
            flash(f'Please check the email it should be {em_ail}. Try Again!')
            return redirect(url_for('contact',stored_text = em_ail))
    return render_template("contact.html", current_user=current_user)

if __name__ == "__main__":
    app.run(debug=True)