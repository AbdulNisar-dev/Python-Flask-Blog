from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import os
from werkzeug.utils import secure_filename     # to secure the uploading file
import math

# opening and Reading the json file we created
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)
'''  Here secret key can be anything ,Set the secret key to some random bytes. Keep this really secret!
'''
app.secret_key = 'super-secret-key'                       # to validate the cookies are legit (used if using session)
app.config['UPLOAD_FOLDER'] = params['upload_location']   # This is to upload files to our database
app.config.update(                                        # for sending emails to the admin about thre entry of
                                                                # info in the database
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    # MAIL_USERNAME = os.environ.get('DB_EMAIL'),
    # MAIL_PASSWORD = os.environ.get('DB_PASSWORD'),

    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_password"]

)

mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)

# Creating a class for uploading the user info from the contact form to the database table we created
class Contacts(db.Model):
    # all the vars are from the database
    s_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    phone_no = db.Column(db.String(120), unique=False, nullable=False)
    msg = db.Column(db.String(120), unique=False, nullable=False)
    date = db.Column(db.String(12), unique=False, nullable=True)

# Creating a class for uploading the posts info from the upload a post form to the database table we created
class Posts(db.Model):
    # all the vars are from the database
    s_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    slug = db.Column(db.String(120), unique=False, nullable=False)
    content = db.Column(db.String(120), unique=False, nullable=False)
    tagline = db.Column(db.String(120), unique=False, nullable=False)
    date = db.Column(db.String(12), unique=False, nullable=True)
    img_file = db.Column(db.String(12), unique=False, nullable=True)

# Managing the no. of posts to be shown in the first index page /( Creating Pagination )
@app.route("/")
def home():

    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #[0: params['no_of_posts']]
    #posts = posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/about")
def about():
    # Below we are rendering/serving/making/giving templates ,and variables from the json file as following
    return render_template("about.html", params=params)


# We can add variable sections to url as shown , the variable is given as keyword argmunet to the func
@app.route("/user/<string:Nissar>")  # here string is a converter to specify the type of the var_
def user(Nissar):
    return "user %s" % Nissar    # here %s means String, %d means int


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    # Checking for user is already login using session which requires a secret key and intialized at top
    if "user" in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    # receiving the login data from the login form by using the request methods
    if request.method == "POST":
        username = request.form.get("uname")
        userpass = request.form.get("pass")

        # if not logged in then checking the credentials used for login in
        if username == params['admin_user'] and userpass == params['admin_password']:
            # set the session variable
            session['user'] = username

            #Used for getting all the posts from database
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    return render_template("login.html", params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)

# making the posts editable
@app.route("/edit/<string:s_no>", methods=['GET', 'POST'])
def edit(s_no):
    # checks for admin's username in the session
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # Adding post if s_no==0
            if s_no == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

            # Here Editing post if s_no !=0
            else:
                post = Posts.query.filter_by(s_no=s_no).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + s_no)

        post = Posts.query.filter_by(s_no=s_no).first()
        return render_template('edit.html', params=params, post=post, s_no=s_no)

# Creating a func to Delete Posts
@app.route("/delete/<string:s_no>", methods=['GET', 'POST'])
def delete(s_no):
    if "user" in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(s_no=s_no).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

# Making a file uploader
@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == 'POST':

            # uploading a file
            '''
                 Uploaded files are stored in memory or at a temporary location on the filesystem.
                 You can access those files by looking at the files attribute on the request object.
                 Each uploaded file is stored in that dictionary. It behaves just like a standard Python file object, 
                 but it also has a save() method that allows you to store that file on the filesystem of the server.
                 
                 If you want to use the filename of the client to store the file on the server, 
                 pass it through the secure_filename() function that Werkzeug provides for you.
            '''
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))


            return "Uploaded Successfully"

# Creating logout button
@app.route("/logout")
def logout():
    # logging out by removing the username from the session if it is in session
    session.pop('user')
    '''  Redirects and Errors:
                To redirect a user to another endpoint, use the redirect() function.
                To abort a request early with an error code, use the abort() function.
    '''
    return redirect('/dashboard')

# Creating a func to collect users info From the contact form
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':

        # Getting user info from the form
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Making entry into the Database
        entry = Contacts(name=name, phone_no=phone, msg=message, date=datetime.now(), email=email)
        #  entry=Contacts(name=name,email=email,phone_no=phone,msg=message)
        db.session.add(entry)
        db.session.commit()

        # sending emails to the adim about the received info from the contact form
        mail.send_message('New Message from ' + name, sender=email,
                          recipients=[params['gmail_user']],
                          # recipients=os.environ.get('DB_EMAIL'),
                          body=message + "\n" + phone
                          )

    return render_template("contact.html", params=params)


app.run(debug=True)
