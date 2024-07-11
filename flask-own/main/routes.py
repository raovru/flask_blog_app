from main.models import User, Posts
from flask import abort, render_template, url_for, flash, redirect, request
from main.forms import RegistrationForm, LoginForm, AccountUpdateForm, PostForm
from main import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import os, secrets
from PIL import Image


@app.route("/")
@app.route("/home")
def home():
    # grab all the posts
    posts = Posts.query.all()
    return render_template('home.html', posts = posts)

@app.route("/about")
def about():
    return render_template('about.html', title = 'About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    # They no longer need to see login and register, if authenticated
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! You can now safely login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(url_for('home'))
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Check credentials again', 'danger')
    return render_template('login.html', title='login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_pic(form_picture):
    # Generate random hex so that image names dont collide
    random_hex = secrets.token_hex(8)
    # split image into name and extension for jpg and png
    _, f_name = os.path.splitext(form_picture.filename)
    # Concat to the name
    pic_f_name = random_hex + f_name
    # Create path in static
    pic_path = os.path.join(app.root_path + '/static/profile_pic', pic_f_name)
    # Resize image:

    # Declare new size
    op_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(op_size)
    # Save
    img.save(pic_path)

    return pic_f_name

@app.route("/account", methods = ['GET', 'POST'])   
@login_required
def account():
    form = AccountUpdateForm()
    user_var = current_user.username
    email_var = current_user.email
    pic_var = current_user.image_file
    if form.validate_on_submit() and user_var == form.username.data and email_var == form.email.data and pic_var == form.picture.data:
        flash("You haven't changed your details!", 'warning')
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
    elif form.validate_on_submit():
        if form.picture.data:
            picture_file = save_pic(form.picture.data)
            current_user.image_file = picture_file
            if pic_var!='default.jpg':
                os.remove(os.path.join(app.root_path, 'static/profile_pic', pic_var))
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated successfully', 'success')

    # we want user's previous username and pw as soon as they try to update
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pic/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route('/post/new', methods = ['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        posts = Posts(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(posts)
        db.session.commit()
        flash('Your post has been published!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Posts.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def post_update(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated", "success")
        return redirect(url_for('post', post_id=post.id))
    
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form)


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))