from flask import Flask, render_template, redirect, make_response, request, flash
from flask import session as login_session

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, StockList, IndustryList, User, Portfolio

import random, string
import httplib2, json, requests

from oauth2client.client import flow_from_clientsecrets, AccessTokenCredentials, FlowExchangeError


###########################
### LOGGING ###############
import logging
from logging.handlers import RotatingFileHandler

logging_handler = RotatingFileHandler( '/home/schlik/webapps/stockmarketsavant/htdocs/logs/stock_market_savant.log' )
logging_handler.setLevel(logging.INFO)
app.logger.addHandler(logging_handler)
###########################






#############################################################
###  SQLAlchemy ORM setup
engine = create_engine('mysql://schlik_db:jizm69@localhost/stocks')
Base.metadata.bind = engine
DBSession = sessionmaker( bind=engine)
session = DBSession()
#############################################################

host = "stockmarketsavant.com"

@app.route('/login')
def showLogin():
    # Create a state token to prevent forgery
    # Store it in the session for later validation.
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    app.logger.info('login_session[state] is %s' % login_session['state'] )
    return render_template('login.html', STATE=state )

@app.route('/createUser')
def createUser():
    if 'handle' not in login_session:
       return redirect( '/login' )
    
    
@app.route('/sector/<string:sector_name>/')
def printSector(sector_name): 
    if 'handle' not in login_session:
       return redirect( '/login' )
    sector_name = sector_name.replace( '_', ' ')
    stock_list = session.query(StockList).filter(StockList.sector==sector_name)
    print sector_name.replace('_',' ' )
    return render_template( 'stock_info.html', stocks = stock_list, sector_name=sector_name.replace('_',' ' ) )

@app.route('/')
def showSectors():
    if 'handle' not in login_session:
       return redirect( '/login' )
    inds =  session.query(IndustryList).all() 
    return render_template( 'sector_info.html', industries = inds, website = host )

@app.route('/gconnect', methods=['POST'])
def gconnect():
     #1 - make sure the 'state' matches
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameters'), 401 )
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data 
    #2 - now get the credentials from Google
    try:
        oauth_flow = flow_from_clientsecrets('/home/schlik/webapps/stockmarketsavant/htdocs/client_secrets.json', scope='' )
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #3 MAGIC - we have a valid access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500 )
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response( json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #Check to see if user is already logged in
    stored_credentials = AccessTokenCredentials(login_session.get('access_token'), 'user-agent-value')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

    ######################################################
    #FINALLY Get to work!
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    #Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt':'json'}

    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if user_id is None :
       response = make_response(json.dumps({'status':'OK','handle':'None'}), 200 )
    else:
       user = getUserInfo(user_id)
       login_session['handle'] =  user.site_handle
       response = make_response(json.dumps({'status':'OK','handle':user.site_handle}), 200 )
    return response



@app.route('/gdisconnect')
def gdisconnect():
    stored_access_token = login_session.get('access_token')
    stored_credentials = AccessTokenCredentials(stored_access_token, 'user-agent-value')

    if stored_credentials is None:
        response = make_response(json.dumps('Current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % stored_access_token

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]


    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['handle']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response( json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/setup_account', methods=['POST'])
def setupAccount():
  
    print request.form['handle_name']
    app.logger.info('setupAccount() : name is %s' %  request.form['handle_name'] )

    if request.args.get('state') != login_session['state']:
        return render_template('poo.html')

    login_session['handle'] =  request.form['handle_name']
    createUser(login_session);
    return redirect( '/' )
    
    



#########################
# User id centric methods
def createUser(login_session):
    newUser = User( site_handle = login_session['handle'], name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add( newUser )
    session.commit()
    user = session.query(User).filter_by( email = login_session['email']).one()
    return user.email

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None
# END User id centric methods
#########################





###############################################################
### FOR REFERENCE                          ####################
###############################################################

#    for stock in  session.query(StockList).filter(StockList.sector=="Health Care").limit(30):


#def application(environ, start_response):
#    app.debug = True
#    app.secret_key = '_J9ltCOY4QBNdFPZNIVuP6Ga'
#    app.run()

if __name__ == '__main__':
    app.debug = True
    app.secret_key = '_J9ltCOY4QBNdFPZNIVuP6Ga'
    app.run( host='0.0.0.0', port = 31776) 


