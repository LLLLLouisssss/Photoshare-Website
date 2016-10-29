######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################
import datetime
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Louis080536'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		birthday=request.form.get('birthday')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (email, password, firstname, lastname, birthday, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, firstname, lastname, birthday, hometown, gender))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=firstname, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	#print cursor.fetchall()
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

#start of album page
@app.route("/album", methods=['GET'])
@flask_login.login_required
def load_album():
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT name FROM Albums WHERE user_id = '{0}'".format(uid))
	albumNames = cursor.fetchall()
	names = []
	for item in albumNames:
		print item
		names.append(item[0])
	if len(names) != 0:
		return render_template('album.html', name=1, album=names)
	else:
		return render_template('album.html')


'''
def getUserAlbums(album_name):
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT album_name FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()
'''
@app.route('/album', methods=['POST'])
@flask_login.login_required

#create an album
def setup_album():
	if request.method == 'POST':
		if request.form['submit'] == 'Create':
			try:
				uid = getUserIdFromEmail(flask_login.current_user.id)
				album_name = request.form.get('album_name')
				create_date = datetime.date.today()
			except:
				print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
				return flask.redirect(flask.url_for('album'))
			cursor = conn.cursor()
			print cursor.execute("INSERT INTO Albums (name, user_id, create_date) VALUES ('{0}', '{1}', '{2}')".format(album_name, uid, create_date))
			conn.commit()
			return render_template('album.html', message='Album Created!')
		elif request.form['submit'] == 'Goto':
			album_name = request.form.get("albums")
			print album_name
			cursor = conn.cursor()
			cursor.execute("SELECT album_id FROM Albums WHERE name = '{0}'".format(album_name))
			album_id = cursor.fetchone()[0] 
			print album_id
			cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
			photo = cursor.fetchall()
			#print photo
			return render_template('photo.html', photos=photo)
'''
#get link name
def getLinkName():
	if request.method == 'POST':
		album_name = request.form.get("albums")
		print album_name
		return album_name
'''

'''
@app.route('/photo', methods=['GET','POST'])
@flask_login.login_required
def show():
	if request.method == 'GET':
		album_name = getLinkName()
		print album_name

#display the photos in that album
def display():
	if request.method == 'POST':
		print 1
		cursor = conn.cursor()
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name = 1
		print album_name
		cursor.execute("SELECT album_id FROM Albums WHERE name = '{0}'".format(album_name))
		album_id = cursor.fetchone()[0] 
		photo = cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
		return render_template('photo.html', photos=photo)
'''


@app.route('/profile', methods=['GET'])
@flask_login.login_required
def protected():
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT email, firstname, lastname, birthday, hometown, gender FROM Users WHERE user_id = '{0}'".format(uid))
	Profile = cursor.fetchall()
	Email, Firstname, Lastname, Birthday, Hometown, Gender = Profile[0]
	return render_template('profile.html', firstname=Firstname, lastname=Lastname, email=Email, birthday=Birthday, hometown=Hometown, gender=Gender)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album_name = request.form.get('albums')
		tag = request.form.get('tag')
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("SELECT album_id FROM Albums WHERE name = '{0}'".format(album_name))
		album_id = cursor.fetchone()[0]
		print album_id
		cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data,uid, caption, album_id))
		conn.commit()
		cursor.execute("SELECT picture_id FROM Pictures WHERE imgdata = '{0}'".format(photo_data))
		picture_id = cursor.fetchone()[0]
		cursor.execute("INSERT INTO storeIn (picture_id, album_id) VALUES ('{0}', '{1}')".format(picture_id, album_id))
		conn.commit()
		cursor.execute("INSERT INTO Tags (tag_text) VALUES ('{0}')".format(tag))
		conn.commit()
		cursor.execute("INSERT INTO associatedWith (picture_id, tag_text) VALUES ('{0}', '{1}')".format(picture_id, tag))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid) )
		#return render_template('upload.html', message="Sorry, you haven't created that album yet! Please create first by click the create link!")
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT name FROM Albums WHERE user_id = '{0}'".format(uid))
		album_name = cursor.fetchall()
		album_names = []
		for item in album_name:
			album_names.append(item[0])
		return render_template('upload.html', albums=album_names, message="If you want to create a new album, please click Create!")

#check if the album exists
def ifAlbumExists(album_name):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT album_id FROM Albums WHERE name = '{0}'".format(album_name)): 
		#this means there are greater than zero entries with that email
		return True
	else:
		return False
#end photo uploading code 


#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
