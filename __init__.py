import os
import random
import string
import json
import httplib2
import requests
from model import Base, User, Category, CatalogItem
from flask import Flask, render_template, request, redirect 
from flask import jsonify, url_for, flash, abort, g, make_response
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import session as login_session
from functools import wraps


# great recommendation from previous udacity reviewer
# helps keep code dry
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
auth = HTTPBasicAuth()
# SQLALCHEMY_DATABASE_URI = "postgresql://yourusername:yourpassword@localhost/yournewdb"
CLIENT_ID = json.loads(open
                       ('/var/www/myapp/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "catalog"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalogitems')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        # print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    # print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@auth.verify_password
def verify_password(username_or_token, password):
    # Try to see if it's a token first
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = session.query(User).filter_by(
            username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@app.route('/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        # print "missing arguments"
        abort(400)

    elif session.query(User).filter_by(username=username).first() is not None:
        # print "existing user"
        user = session.query(User).filter_by(username=username).first()
        return jsonify({'message': 'user already exists'}), 200
    else:
        user = User(username=username)
        user.hash_password(password)
        session.add(user)
        session.commit()
        return jsonify({'username': user.username}), 201


@app.route('/api/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@app.route('/api/json')
@auth.login_required
def get_resource():
    categories = session.query(Category).all()
    items = session.query(CatalogItem).all()
    user = session.query(User).all()
    return jsonify({'data': 'Hello, %s!' % g.user.username},
                   [i.serialize for i in categories],
                   [i.serialize for i in items],
                   [i.serialize for i in user])


# Show all categories
@app.route('/')
@app.route('/category/')
def showCategories():
    categories = session.query(Category).order_by(Category.name)
    if 'username' not in login_session:
        return render_template('publiccategories.html', categories=categories)
    else:
        return render_template('categories.html', categories=categories)


# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    editedCategory = session.query(
        Category).filter_by(id=category_id).one()
    if editedCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not " \
               "authorized to edit this category. Please create your own " \
               "category in order to edit.');}</script>" \
               "<body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Successfully Updated %s' % editedCategory.name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not" \
               " authorized to delete this category. Please create " \
               "your own category in order to delete.');}</script>" \
               "<body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCategories', category_id=category_id))
    else:
        return render_template('deleteCategory.html',
                               category=categoryToDelete)


# Show a category catalog
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/catalog/')
def showCatalog(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(category.user_id)
    items = session.query(CatalogItem).filter_by(
        category_id=category_id).all()
    if 'username' not in login_session or creator.id != login_session[
            'user_id']:
        return render_template('publiccatalog.html', items=items,
                               category=category, creator=creator)
    else:
        return render_template('catalog.html', items=items, category=category,
                               creator=creator)


# Create a new catalog item
@app.route('/category/<int:category_id>/catalog/new/', methods=['GET', 'POST'])
@login_required
def newCatalogItem(category_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not " \
               "authorized to add catalog items to this category. " \
               "Please create your own category in order to add items.');}" \
               "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = CatalogItem(name=request.form['name'],
                              description=request.form['description'],
                              category_id=category_id,
                              user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash('New Catalog %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCatalog', category_id=category_id))
    else:
        return render_template('newcatalogitem.html', category_id=category_id)


# Edit a catalog item
@app.route('/category/<int:category_id>/catalog/<int:catalog_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editCatalogItem(category_id, catalog_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    editedItem = session.query(CatalogItem).filter_by(id=catalog_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorized" \
               " to edit catalog items to this category. Please " \
               "create your own category in order to edit items.');}" \
               "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Catalog Item Successfully Updated!')
        return redirect(url_for('showCatalog', category_id=category_id,
                                catalog_id=catalog_id))
    else:
        return render_template('editcatalogitem.html', category_id=category_id,
                               catalog_id=catalog_id, item=editedItem)


# Delete a catalog item
@app.route('/category/<int:category_id>/catalog/<int:catalog_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteCatalogItem(category_id, catalog_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(CatalogItem).filter_by(id=catalog_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not " \
               "authorized to delete catalog items to this category. " \
               "Please create your own category in order to delete" \
               " items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Catalog Item Successfully Deleted')
        return redirect(url_for('showCatalog', category_id=category_id))
    else:
        return render_template('deleteCatalogItem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            # del login_session['credentials']

        # for facebook future addon
        # if login_session['provider'] == 'facebook':
        #     fbdisconnect()
        #     del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = 'love_it'
    app.run()
   
    
