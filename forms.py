from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, HiddenField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField('Submit Comment')

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()], render_kw={"autofocus": True})
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")

class AdminLoginForm(FlaskForm):
    email = StringField("User Id", validators=[DataRequired()], render_kw={"autofocus": True})
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()], render_kw={"autofocus": True})
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

class AdminContactForm(FlaskForm):
    email = StringField("User Email")
    reply = CKEditorField("Reply")
    submit = SubmitField("Send")
    form_name = HiddenField(default="admin_contact_form")

class ResolvedQueryForm(FlaskForm):
    resolved = SelectField("Query Resolved", choices=[], validate_choice=False)
    submit = SubmitField("Resolved")
    form_name = HiddenField(default="resolved_query_form")