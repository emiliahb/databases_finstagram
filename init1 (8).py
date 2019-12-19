# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import os
import hashlib
import time


# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password='',
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

# Define a route to hello function
@app.route('/')
def hello():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if (data):
        # creates a session for the the user
        # session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s)'
        cursor.execute(ins, (username, password))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT postingdate, photoPoster, photoID, caption, Photo.filePath, allFollowers FROM Photo Natural Join sharedWith Natural Join belongto WHERE photoposter = %s UNION SELECT postingdate, photoPoster, photoID, caption, Photo.filePath, allFollowers From Photo Join Follow On (Photo.photoPoster = Follow.username_followed) WHERE (username_follower = %s AND followstatus = 1) ORDER BY postingdate DESC' # Natural Join Tag GROUP BY photoID
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    query2 = 'SELECT * FROM Tagged Natural Join Person WHERE tagstatus = 1'
    cursor.execute(query2)
    tagData = cursor.fetchall()


    groupNameQuery = 'SELECT DISTINCT groupName, groupOwner FROM Friendgroup WHERE groupOwner = %s'
    cursor.execute(groupNameQuery, (user))
    groupNameData = cursor.fetchall()

    FriendsQuery = 'SELECT * FROM belongto Natural Join Friendgroup WHERE groupOwner = %s'
    cursor.execute(FriendsQuery, (user))
    FriendsData = cursor.fetchall()


    cursor.close()
    return render_template('home.html', username=user, posts=data, tagPosts = tagData, FriendsData = FriendsData, FriendsGroupNameData = groupNameData)



@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    filepath = request.form['filepath']
    caption = request.form['caption']
    if request.form.get('visible'):
        visible = '1'
    else:
        visible = '0'
    query = 'INSERT INTO Photo (photoPoster, filePath, caption, allFollowers) VALUES(%s, %s, %s, %s )'
    cursor.execute(query, (username, filepath, caption, visible))
    conn.commit()
    cursor.close()
    cursor = conn.cursor();
    i = 1;
    while request.form.get(str(i)):
        # getting groupName
        group = request.form.get(str(i))
        # getting owner_username
        query = "SELECT owner_username from BelongTo where groupName = '" + group + "' and username = '" + username + "' or owner_username = '" + username + "';"
        cursor.execute(query)
        owner = cursor.fetchall()
        # getting photoID
        query = "SELECT photoID FROM Photo where photoPoster = '" + username + "' ORDER BY photoID DESC LIMIT 1;"
        cursor.execute(query)
        id = cursor.fetchall()
        # inserting into Share
        query = "INSERT INTO sharedWith VALUES(%s,%s,%s)"
        cursor.execute(query, (str(group), str(owner[0]['owner_username']), id[0]['photoID']))
        i += 1
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/manage')
def manage():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM Tagged NATURAL JOIN Photo WHERE tagstatus = 0 AND username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchall()

    query2 = 'SELECT * FROM Follow WHERE followstatus = 0 AND username_follower = %s'
    cursor.execute(query2, (username))
    requestData = cursor.fetchall()

    cursor.close()
    return render_template('manage.html', tagData=data, requestData = requestData)


@app.route('/select_blogger')
def select_blogger():
    # check that user is logged in
    # username = session['username']
    # should throw exception if username not found

    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM Person'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)


@app.route('/show_posts', methods=["GET", "POST"])
def show_posts(selected=None):
    user = session['username']
    cursor = conn.cursor();
    query = "SELECT Photo.photoID,photoPoster,postingdate,filePath,caption FROM Photo NATURAL JOIN sharedWith NATURAL JOIN Friendgroup NATURAL JOIN BelongTo WHERE (photoposter = %s OR BelongTo.owner_username = %s) AND photoPoster = %s UNION (SELECT photoID, photoPoster, postingdate, filePath, caption FROM Photo JOIN Follow ON photoPoster = username_followed WHERE username_follower = %s and followstatus= 1 and photoPoster = %s) ORDER BY postingdate DESC ;"
    cursor.execute(query, (user, user, selected, user, selected))
    data = cursor.fetchall()
    print(data)
    # selecting tags
    query = 'SELECT q.photoID,Person.username, firstName, lastName FROM (SELECT Photo.photoID,photo.photoPoster FROM Photo NATURAL JOIN sharedWith NATURAL JOIN Friendgroup NATURAL JOIN BelongTo WHERE BelongTo.member_username = %s OR BelongTo.owner_username = %s) as q JOIN Tagged JOIN Person ON q.photoID = Tagged.photoID and Tagged.username = Person.username WHERE tagstatus = 1 and photoPoster = %s UNION (SELECT t.photoID,Person.username, firstName, lastName FROM (SELECT Photo.photoID,Photo.photoPoster FROM Photo JOIN Follow ON photoPoster = username_followed WHERE username_follower = %s and followstatus = 1) as t JOIN Tagged JOIN Person ON t.photoID = Tagged.photoID and Tagged.username = Person.username WHERE tagstatus = 1 and photoPoster = %s)'
    cursor.execute(query, (user, user, selected, user, selected))
    tags = cursor.fetchall()
    query = "SELECT photoID FROM likes WHERE username = %s"
    cursor.execute(query, (user))
    liked_posts = cursor.fetchall()
    return render_template('show_posts.html', username=user, profile=selected, posts=data, tagged=tags,
                           likes=liked_posts)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)