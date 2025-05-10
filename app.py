from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
import smtplib
import pandas as pd
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from random import randint
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, and_,Boolean 
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, AdminLoginForm, AdminContactForm, ResolvedQueryForm
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv
import os
load_dotenv()

count = 5
em_ail = None
unique_id = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

my_email = os.getenv("EMAIL")
password = os.getenv("EMAIL_PASSWORD")

ckeditor = CKEditor(app)
Bootstrap5(app)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=15)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 1800 
}
db = SQLAlchemy(model_class=Base, engine_options=app.config['SQLALCHEMY_ENGINE_OPTIONS'])
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost", back_populates="author")
    user_posts = relationship("UserPost", back_populates="author") 
    comments = relationship("Comment", back_populates="comment_author")

class UserPost(db.Model):
    __tablename__ = "user_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="user_posts")
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    

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
    Ref_no: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(250), nullable=True)

class AdminContact(db.Model):
    __tablename__ = "adminqueries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    Ref_no: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(10))
    reply: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    

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
    unique_id = int(user_id)
    em_ail = db.session.execute(db.select(User.email).where(User.id==user_id)).scalar()
    return db.get_or_404(User, user_id)

def is_valid_email(email):
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
        
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        elif is_valid_email(form.email.data):
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
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                        connection.starttls()
                        connection.login(user=my_email, password=password)
                        connection.sendmail(
                            from_addr=my_email,
                            to_addrs=form.email.data,
                            msg=f"Subject:Thank you for signing up at @BlogFocus your account is created.\n\nHi {form.name.data.capitalize()},\n\nI welcome you to BlogFocus family.\n\nRegards,\nRichard Samuel\nDeveloper @BlogFocus"
                        )
            except Exception as e:
                    app.logger.error(f"Error sending email: {e}")
                    flash(f"Please enter a valid Email !!! err: {e}", category="error")
                    return redirect(url_for('register'))
            
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        else:
            flash("Please enter a valid email")
            redirect(url_for('register'))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/profile/<curr_user>', methods=["GET", "POST"])
def user(curr_user):
    form = User()
    
    return render_template("user.html", form=form, userd=curr_user)

@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    form = AdminLoginForm()
    global count
    if form.validate_on_submit():
        email = form.email.data
        result = db.session.execute(db.select(User).where(and_(User.email == email, User.id == 1)))
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
        if not user:
            flash("Email does not exist, please register.")
            return redirect(url_for('login'))
        if user.email == 'samuelard715@outlook.com':
            flash('Please go to admin login tab to log in as a admin..')
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
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def show_post(post_id):
    from_admin = request.args.get('from_admin') 
    if current_user.id != 1 and current_user.is_authenticated:
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
    elif current_user.id == 1 and from_admin == "true":    
        requested_post = db.get_or_404(UserPost, post_id)
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
    elif current_user.id == 1 and request.endpoint == "show_post":
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

@app.route("/deletequery/<int:post_id>")
@admin_only
def deletequery(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('admincontact'))

@app.route("/contact-admin", methods=["GET", "POST"])
@admin_only
def admincontact():
    form = AdminContactForm()
    resolved_form = ResolvedQueryForm()

    
    contact_queries = db.session.execute(db.select(Contact.Ref_no)).scalars().all()
    resolved_form.resolved.choices = [("", "Select Query number")] + [(str(ref_no), str(ref_no)) for ref_no in contact_queries]

    if request.method == "POST":
        
        if form.form_name.data == "admin_contact_form" and form.validate_on_submit():
            email = form.email.data
            message = form.reply.data

            user = db.session.execute(db.select(Contact).with_only_columns(Contact.Ref_no, Contact.name, Contact.mobile).where(Contact.email == email))
            resulty = user.first()
            
            try:
                Query_no = resulty.Ref_no
                
                with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                    connection.starttls()
                    connection.login(user=my_email, password=password)
                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=email,
                        msg=f"Subject:This is with reference #{Query_no} \n\nDear {resulty.name}, \nThank you for contacting BlogFocus! \n{message} \n\n\n Feel free to contact again. \n\n Richard Samuel \n Developer @BlogFocus "
                    )

                new_query = AdminContact(
                    Ref_no=Query_no,
                    name=resulty.name,
                    email=email,
                    mobile=resulty.mobile,
                    reply=message,
                    date=date.today().strftime("%B %d, %Y")
                )

                db.session.add(new_query)
                db.session.commit()
                flash('Successfully Sent.', category="success")
                return redirect(url_for('admincontact'))
            except Exception as e:
                app.logger.error(f"Error sending email: {e}")
                flash(f"An error occurred while sending the email. Please try again later.\n error: {e}", category="error")
                return redirect(url_for('admincontact'))

        elif resolved_form.form_name.data == "resolved_query_form" and resolved_form.validate_on_submit():
            try:
                resolved = int(resolved_form.resolved.data)
                if resolved:
                    delete_query = db.session.execute(db.select(Contact).with_only_columns(Contact.id, Contact.Ref_no).where(Contact.Ref_no == resolved)).first()
                    admin_deletequery = db.session.execute(db.select(AdminContact).with_only_columns(AdminContact.id, AdminContact.Ref_no).where(AdminContact.Ref_no == resolved)).first()
                    if delete_query:
                        admin_querydelete = db.get_or_404(AdminContact, admin_deletequery.id)
                        query_to_delete = db.get_or_404(Contact, delete_query.id)
                        db.session.delete(query_to_delete)
                        db.session.delete(admin_querydelete)
                        db.session.commit()
                        flash(f'Query with Ref_no #{resolved} Resolved.', category="success")
                        return redirect(url_for('admincontact'))
                    else:
                        flash("Please select the Ref_no")
                        return redirect(url_for('admincontact'))
            except:
                flash('Please select the Ref_no')
                return redirect(url_for('admincontact'))

 
    result = db.session.execute(db.select(Contact))
    query = [[c.Ref_no, c.name, c.email, c.mobile, c.message, c.date] for c in result.scalars()]
    columns = ["Ref_No", "Name", "Email", "Mobile", "Message", "Date"]
    df = pd.DataFrame(query, columns=columns)
    table_html = df.to_html(classes="table table-striped table-bordered", index=False)

    return render_template("Admincontact.html", current_user=current_user, form=form, resolvedform=resolved_form, query=table_html)

@app.route("/admin-approval", methods=["GET", "POST"])
@admin_only
def adminapproval():
    result = db.session.execute(db.select(UserPost))
    posts = result.scalars().all()
    return render_template("admin_approval.html", all_posts=posts, current_user = current_user)

@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if unique_id != 1:
        if form.validate_on_submit():
            new_post = UserPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            db.session.commit()
            try:
                user_msg = MIMEMultipart()
                user_msg['From'] = my_email
                user_msg['To'] = em_ail
                user_msg['Subject'] = f"We received your request for blog post titled: {form.title.data}"

                user_body = f"""Dear {current_user.name},\n\n
            Thank you for posting on BlogFocus!\n\n
            We will post it after validation.\n\n
            Thank you,\n
            Richard Samuel\n
            Developer @BlogFocus"""
                user_msg.attach(MIMEText(user_body, 'plain', 'utf-8'))

                with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                    connection.starttls()
                    connection.login(user=my_email, password=password)
                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=em_ail,
                        msg=user_msg.as_string()
                    )
                admin_msg = MIMEMultipart()
                admin_msg['From'] = my_email
                admin_msg['To'] = my_email
                admin_msg['Subject'] = f"{current_user.name} requested for blog post titled: {form.title.data}"

                admin_body = f"""Please visit blogfocus@vercel.app Admin Tab to validate the post!"""
                admin_msg.attach(MIMEText(admin_body, 'plain', 'utf-8'))

                
                with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                    connection.starttls()
                    connection.login(user=my_email, password=password)
                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=my_email,
                        msg=admin_msg.as_string()
                    )
            except Exception as e:
                app.logger.error(f"Error sending email: {e}")
                flash(f"An error occurred while adding the post. Please try again later.")
                return redirect(url_for("add_new_post"))
            
            flash("Your post will go live once approved by the Admin.")
            return redirect(url_for("get_all_posts"))
    else:
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

@app.route("/admin-decision/<int:post_id>")
@login_required
def admin_decision(post_id):
    decision = request.args.get('decision')
    print(decision)
    post_to_delete = db.get_or_404(UserPost, post_id)
    search__user_email = db.session.execute(db.select(User.email,User.name).where(User.id == post_to_delete.author_id)).first()
    if decision == 'rejected':
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                    connection.starttls()
                    connection.login(user=my_email, password=password)
                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=search__user_email.email,
                        msg = f"Subject:Your Post Has Been Rejected\n\nDear {search__user_email.name},\n\nThank you for posting on BlogFocus!\n\nUnfortunately, your content has some issues.\n\nWe urge you to submit it again and contact us through the Contact tab to know the reason for the rejection.\n\nRegards,\nRichard Samuel\nDeveloper @BlogFocus"
                    )
        db.session.delete(post_to_delete)
        db.session.commit()
        flash(f"Post '{post_to_delete.id}' has been rejected.", category="error")
        return redirect(url_for('adminapproval'))
    elif decision == 'approved':
        new_post = BlogPost(
            title=post_to_delete.title,
            subtitle=post_to_delete.subtitle,
            body=post_to_delete.body,
            img_url=post_to_delete.img_url,
            author=post_to_delete.author,
            date=post_to_delete.date
        )    
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                    connection.starttls()
                    connection.login(user=my_email, password=password)
                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=search__user_email.email,
                        msg=f"Subject:You post has been approved !!!\n\nDear {search__user_email.name}, \nThank you for posting on BlogFocus! \n\n\n Your post is live. \n\n Happy Blogging, \n Richard Samuel \n Developer @BlogFocus "
                    )
        db.session.add(new_post)    
        db.session.delete(post_to_delete)
        db.session.commit()
        flash(f"Post '{post_to_delete.id}' has been approved.")
        return redirect(url_for('adminapproval'))
    return redirect(url_for('adminapproval'))

@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    result = db.session.execute(db.select(Contact.date, Contact.Ref_no, Contact.message, AdminContact.reply).join(AdminContact, Contact.Ref_no == AdminContact.Ref_no).where(Contact.email == em_ail))
    query = [[c.date, c.Ref_no, c.message, c.reply] for c in result]
    if query:
        columns = ["Date","Ref_No","Your Message","Reply"]
        df = pd.DataFrame(query, columns=columns)
        table_html = df.to_html(classes="table table-striped table-bordered", index=True,border=0).replace('<th>', '<th style="text-align: left;">')
    else:
        table_html = ""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        Query_no = randint(1,9999)
        if unique_id == None:
            flash('Please login in to contact..')
            return redirect(url_for('login'))
        result = db.session.execute(db.select(User).where(User.id == unique_id))
        user = result.scalar()
        if unique_id == user.id and email == em_ail:
            existing_query = db.session.execute(db.select(Contact).with_only_columns(Contact.Ref_no, Contact.name).where(Contact.email == email)).first()
            if existing_query:
                flash(f'Query already existed for the user {existing_query.name} with Ref_no #{existing_query.Ref_no}. Please do not initiate again!')
                return redirect(url_for('contact'))
            else:
                new_query = Contact(
                    name=name,
                    Ref_no=Query_no,
                    email=email,
                    mobile=phone,
                    message=message,
                    date=date.today().strftime("%B %d, %Y")
                    )
                db.session.add(new_query)
                db.session.commit()
                try:
                    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                        connection.starttls()
                        connection.login(user=my_email, password=password)
                        connection.sendmail(from_addr=email, to_addrs=my_email,
                                    msg=f"Subject:{name} sends a message\n\n User Query : {message} \n\n\n Mob:{phone}\n\n\n Please visit blogfocus.vercel.app Admin Tab to address it")
                        connection.sendmail(
                        from_addr=my_email,
                        to_addrs=email,
                        msg=f"Subject:Your query has been initiated with reference id {Query_no} \n\nDear {name}, \nThank you for contacting BlogFocus! \nYou will Hear from us within 24 working hours. \n\n\n Thank you. \n\n Richard Samuel \n Developer @BlogFocus "
                        )
                    flash('Successfully Sended please check your inbox/spam folder.',category="success")
                    return redirect(url_for('contact'))
                except Exception as e:
                    app.logger.error(f"Error sending email: {e}")
                    flash(f"An error occurred while sending the email. Please try again later.\n error: {e}", category="error")
                    return redirect(url_for('contact'))
        else:
            flash(f'Please check the email it should be {em_ail}. Try Again!')
            return redirect(url_for('contact',stored_text = em_ail))
    return render_template("contact.html", current_user=current_user, userquery = table_html)

if __name__ == "__main__":
    app.run(debug=True)