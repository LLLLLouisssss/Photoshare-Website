######################################
# author Zonekun Liu <liuzk@bu.edu> 
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
			#print album_id
			cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
			photos = cursor.fetchall()
			tags = []
			Map = {}
			for photo in photos:
				imgdata, picture_id, caption = photo
				print picture_id
				cursor.execute("SELECT tag_text FROM associatedWith WHERE picture_id = '{0}'".format(picture_id))
				tag = cursor.fetchone()[0]
				print tag
				tag = tag.split('#')
				tags.append(tag)
				print tag
				Map[photo] = tag 
			return render_template('photo.html', Map=Map) 
		elif request.form['submit'] == 'Delete':
			album_name = request.form.get("albums")
			cursor = conn.cursor()
			cursor.execute("SELECT album_id FROM Albums WHERE name = '{0}'".format(album_name))
			album_id = cursor.fetchone()[0] 
			cursor.execute("DELETE FROM Albums WHERE album_id ='{0}'".format(album_id))
			conn.commit()
			return render_template('album.html', message='Album Deleted!')


#Delete a photo of yours
@app.route('/deletePhoto/<picture_id>', methods=['GET', 'POST'])
@flask_login.login_required
def deletePhoto(picture_id):
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Pictures WHERE Picture_id ='{0}'".format(picture_id))
		conn.commit()
		'''
		cursor.execute("DELETE FROM storeIn WHERE Picture_id ='{0}'".format(picture_id))
		conn.commit()
		cursor.execute("DELETE FROM Comments WHERE Picture_id ='{0}'".format(picture_id))
		conn.commit()
		cursor.execute("DELETE FROM leaveComments WHERE Picture_id ='{0}'".format(picture_id))
		conn.commit()
		cursor.execute("DELETE FROM associatedWith WHERE Picture_id ='{0}'".format(picture_id))
		conn.commit()
		'''
		return render_template('album.html', message="You have deleted the photo!")



#Display all photos from database
@app.route('/allphotos', methods=['GET', 'POST'])
#@flask_login.login_required
def showPhotos():
	if request.method == 'GET':
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, picture_id, user_id, caption, num_likes FROM Pictures")
		photos = cursor.fetchall()
		Map = {}
		for photo in photos:
			cursor.execute("SELECT comment_text FROM Comments WHERE picture_id ='{0}'".format(photo[1]))
			comment_text = cursor.fetchall()
			print comment_text
			if (len(comment_text) != 0):
				Map[photo] = comment_text
			else:
				Map[photo] = ""
		return render_template('allphotos.html', photos=Map)

#like a photo
@app.route('/like/<picture_id>', methods=['GET', 'POST'])
@flask_login.login_required	
def likePhotos(picture_id):
	cursor = conn.cursor()
	cursor.execute("UPDATE Pictures SET num_likes = num_likes + 1 WHERE picture_id ='{0}'".format(picture_id))
	conn.commit()
	cursor.execute("SELECT imgdata, picture_id, user_id, caption, num_likes FROM Pictures")
	photos = cursor.fetchall()
	Map = {}
	for photo in photos:
		cursor.execute("SELECT comment_text FROM Comments WHERE picture_id ='{0}'".format(photo[1]))
		comment_text = cursor.fetchall()
		print comment_text
		if (len(comment_text) != 0):
			Map[photo] = comment_text
		else:
			Map[photo] = ""
	return render_template('allphotos.html', message='You have liked a photo!', photos=Map)

#leave a comment to a photo
@app.route('/leaveComments/<picture_id>', methods=['GET', 'POST'])
#@flask_login.login_required	
def leaveComments(picture_id):
	if request.method == 'POST':
		#if (User.is_authenticated):
		uid = getUserIdFromEmail(flask_login.current_user.id)
		#else:
		#	uid = 0
		comment_text = request.form.get('description')
		cursor = conn.cursor()
		if not cursor.execute("SELECT * FROM Pictures WHERE picture_id ='{0}' and user_id= '{1}'".format(picture_id,uid)):
			cursor.execute("INSERT INTO Comments (comment_text, picture_id, user_id) VALUES ('{0}', '{1}','{2}')".format(comment_text,picture_id,uid))
			conn.commit()
			cursor.execute("UPDATE Users SET contribution = contribution + 1 WHERE user_id ='{0}'".format(uid))
			conn.commit()
			cursor.execute("SELECT comment_id FROM Comments WHERE comment_text = '{0}' and picture_id ='{1}' and user_id= '{2}'".format(comment_text,picture_id,uid))
			comment_id = cursor.fetchone()[0]
			print comment_id
			cursor.execute("INSERT INTO leaveComments (comment_id, picture_id) VALUES ('{0}', '{1}')".format(comment_id,picture_id))
			conn.commit()
			cursor.execute("SELECT imgdata, picture_id, user_id, caption, num_likes FROM Pictures")
			photos = cursor.fetchall()
			Map = {}
			for photo in photos:
				cursor.execute("SELECT comment_text FROM Comments WHERE picture_id ='{0}'".format(photo[1]))
				comment_text = cursor.fetchall()
				print comment_text
				if (len(comment_text) != 0):
					Map[photo] = comment_text
				else:
					Map[photo] = ""
			return render_template('allphotos.html', message='You have left your comment to the photo!', photos=Map)
		else:
			cursor = conn.cursor()
			cursor.execute("SELECT imgdata, picture_id, user_id, caption, num_likes FROM Pictures")
			photos = cursor.fetchall()
			Map = {}
			for photo in photos:
				cursor.execute("SELECT comment_text FROM Comments WHERE picture_id ='{0}'".format(photo[1]))
				comment_text = cursor.fetchall()
				print comment_text
				if (len(comment_text) != 0):
					Map[photo] = comment_text
				else:
					Map[photo] = ""
			return render_template('allphotos.html', message='You can not leave a comment to your own photo!', photos=Map)
	else:
		'''
		cursor = conn.cursor()
		cursor.execute("SELECT imgdata, picture_id, user_id, caption, num_likes FROM Pictures")
		photos = cursor.fetchall()
		Map = {}
		for photo in photos:
			cursor.execute("SELECT comment_text FROM Comments WHERE picture_id ='{0}'".format(photo[1]))
			comment_text = cursor.fetchall()
			print comment_text
			if (len(comment_text) != 0):
				Map[photo] = comment_text
			else:
				Map[photo] = ""
		return render_template('allphotos.html', photos=Map, picture_id=picture_id)
		'''
		return render_template('comments.html', picture_id=picture_id)
'''
#show all comments of the photo 
@app.route('/showComments/<picture_id>', methods=['GET', 'POST'])
@flask_login.login_required	
def showComments(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT comment_text FROM Comments WHERE picture_id ='{0}'".format(photo[1]))
	comment_text = cursor.fetchall()
	cursor.execute("SELECT imgdata, picture_id, user_id, caption, num_likes FROM Pictures")
	photos = cursor.fetchall()
	return render_template('allphotos.html', message='You have liked a photo!', photos=photos)
'''
#View your photos with the chosen tag
@app.route('/yourtag', methods=['GET', 'POST'])
@flask_login.login_required
def showYourPictures():
	if request.method == 'POST':
		if request.form['submit'] == 'Goto':
			tag_text = request.form.get("tags")
			print tag_text
			uid = getUserIdFromEmail(flask_login.current_user.id)
			print uid
			cursor = conn.cursor()
			cursor.execute("SELECT picture_id FROM Pictures WHERE user_id = '{0}'".format(uid))
			pids = cursor.fetchall()
			print pids
			tmps = []
			for pid in pids:
				cursor.execute("SELECT picture_id, tag_text FROM associatedWith WHERE picture_id = '{0}'".format(pid[0]))
				tmp = cursor.fetchone()
				print tmp
				tmps.append(tmp)
			print tmps
			picture_ids = []
			for tmp in tmps:
				picture_id, tags = tmp
				print picture_id, tags
				if (tag_text in tags):
					picture_ids.append(picture_id)
			print picture_ids
			Map = {}
			for picture_id in picture_ids:
				cursor.execute("SELECT imgdata, user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
				imgdata, user_id = cursor.fetchone()
				cursor.execute("SELECT firstname, lastname FROM Users WHERE user_id = '{0}'".format(user_id))
				user = cursor.fetchone()
				print user
				firstname, lastname = user
				name = (str(firstname) + ' ' + str(lastname))
				print name
				Map[imgdata] = name
			return render_template('tag.html', Map=Map) 

@app.route('/tag', methods=['GET', 'POST'])
#@flask_login.login_required
def showPictures():
	if request.method == 'POST':
		if request.form['submit'] == 'Goto':
			tag_text = request.form.get("tags")
			print tag_text
			cursor = conn.cursor()
			cursor.execute("SELECT picture_id, tag_text FROM associatedWith")
			tmps = cursor.fetchall()
			print tmps
			picture_ids = []
			for tmp in tmps:
				picture_id, tags = tmp
				print picture_id, tags
				if (tag_text in tags):
					picture_ids.append(picture_id)
			print picture_ids
			Map = {}
			for picture_id in picture_ids:
				cursor.execute("SELECT imgdata, user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
				imgdata, user_id = cursor.fetchone()
				cursor.execute("SELECT firstname, lastname FROM Users WHERE user_id = '{0}'".format(user_id))
				user = cursor.fetchone()
				print user
				firstname, lastname = user
				name = (str(firstname) + ' ' + str(lastname))
				print name
				Map[imgdata] = name
			return render_template('tag.html', Map=Map)
		elif request.form['submit'] == 'Search':
			tag_text = request.form.get("inputTags")
			if (tag_text.split('#')):
				tag_text = tag_text.split('#')
			cursor = conn.cursor()
			cursor.execute("SELECT picture_id, tag_text FROM associatedWith")
			tmps = cursor.fetchall()
			Map = []
			for tag in tag_text:
				num = 0
				photos = []
				for tmp in tmps:
					picture_id, tags = tmp
					if (tag in tags):
						photos.append(tmp)
				if len(photos) == 0:
					return render_template('tag.html', message="Sorry no pictures contain all the tags, please re-type something else!")
				else:
					Map.append(photos)
			print Map
			Photo = {}
			i = 0
			for Tuple in Map[0]:
				num = 0
				for List in Map:
					if (Tuple in List):
						num = num + 1
				if (num == len(Map)):
					i = 1
					picture_id, tags = Tuple
					cursor.execute("SELECT imgdata, user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
					imgdata, user_id = cursor.fetchone()
					cursor.execute("SELECT firstname, lastname FROM Users WHERE user_id = '{0}'".format(user_id))
					user = cursor.fetchone()
					firstname, lastname = user
					name = (str(firstname) + ' ' + str(lastname))
					Photo[imgdata] = name
			if (i == 0):
				return render_template('tag.html', message="Sorry no pictures contain all the tags, please re-type something else!")
			else:
				return render_template('tag.html', Map=Photo)

	else:
		cursor = conn.cursor()
		cursor.execute("SELECT tag_text FROM associatedWith")
		tags = cursor.fetchall()
		Tags = []
		num = []
		Map = []
		for item in tags:
			item = item[0]
			if (item.split('#')):
				item = item.split('#')
				#print item
				for i in range(len(item)):
					tmp = item[i]
					if (tmp not in Tags):
						Tags.append(tmp)
			else:
				if (item not in Tags):
					Tags.append(item)
		print tags
		for tag in Tags:
			i = 0
			for text in tags:
				if tag in text[0]:
					i = i + 1
			num.append(i)
			Map.append([tag, i])
		Map.sort(key=lambda tup: tup[1], reverse=True)
		print Map
		return render_template('tag.html', tags=Map) 
		#print tag_text


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
		cursor.execute("UPDATE Users SET contribution = contribution + 1 WHERE user_id ='{0}'".format(uid))
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

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
#list your friends

#add a new friend
def addFriend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	#print uid
	cursor = conn.cursor()
	if request.method == 'POST':
		test = 1
		if request.form['submit'] == 'Search':
			Email = request.form.get('email')
			if cursor.execute("SELECT firstname, lastname FROM Users WHERE email = '{0}'".format(Email)):
				user = cursor.fetchone()
				firstname, lastname = user
				name = (str(firstname) + ' ' + str(lastname))
				test = 1
				return render_template('friends.html', user=name, Email=Email)
			else:
				return render_template('friends.html', message="This email has not been registerd!")
		elif request.form['submit'] == 'View':
			Email = request.form.get('Email')
			#print email
			if test:
				cursor.execute("SELECT email, firstname, lastname, birthday, hometown, gender FROM Users WHERE email = '{0}'".format(Email))
				Profile = cursor.fetchone()
				Email, Firstname, Lastname, Birthday, Hometown, Gender = Profile
				return render_template('profile.html', firstname=Firstname, lastname=Lastname, email=Email, birthday=Birthday, hometown=Hometown, gender=Gender)
			else:
				return render_template('friends.html', message="This email has not been registerd!")
		elif request.form['submit'] == 'Add':
			Email = request.form.get('Email')
			if test:
				cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(Email))
				my_id = uid
				friend_id = cursor.fetchone()[0]
				#print user2_id
				user_id = []
				cursor.execute("SELECT user2_id FROM friendTo WHERE user1_id = '{0}'".format(uid))
				user2_ids = cursor.fetchall()
				if len(user2_ids) != 0:
					for user2_id in user2_ids:
						user2_id = user2_id[0]
						print user2_id
						user_id.append(user2_id)

				cursor.execute("SELECT user1_id FROM friendTo WHERE user2_id = '{0}'".format(uid))
				user1_ids = cursor.fetchall()
				if len(user1_ids) != 0:
					for user1_id in user1_ids:
						user1_id = user1_id[0]
						print user1_id
						user_id.append(user1_id)
				print user_id
				if (friend_id not in user_id):
					cursor.execute("INSERT INTO friendTo (user1_id, user2_id) VALUES ('{0}', '{1}')".format(my_id, friend_id))
					conn.commit()
					return render_template('friends.html', message="Addedd successfully!")
				else:
					return render_template('friends.html', message="You have already added this user as your friend!")
			else:
				return render_template('friends.html', message="This email has not been registerd!")
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		user_id = []
		cursor = conn.cursor()
		cursor.execute("SELECT user2_id FROM friendTo WHERE user1_id = '{0}'".format(uid))
		user2_ids = cursor.fetchall()
		if len(user2_ids) != 0:
			for user2_id in user2_ids:
				user2_id = user2_id[0]
				print user2_id
				user_id.append(user2_id)

		cursor.execute("SELECT user1_id FROM friendTo WHERE user2_id = '{0}'".format(uid))
		user1_ids = cursor.fetchall()
		if len(user1_ids) != 0:
			for user1_id in user1_ids:
				user1_id = user1_id[0]
				print user1_id
				user_id.append(user1_id)
		print user_id
		names = []
		if len(user_id) != 0:
			for fid in user_id:
			 	cursor.execute("SELECT firstname, lastname FROM Users WHERE user_id = '{0}'".format(fid))
			 	user = cursor.fetchone()
			 	firstname, lastname = user
			 	name = (str(firstname) + ' ' + str(lastname))
			 	names.append(name)
			return render_template('friends.html', friends=names, message1="Here are your friends!", search=1)
		else:
			return render_template('friends.html', message1="Seems like you haven't added any friends so far!")


#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
