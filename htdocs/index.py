from flask import Flask, render_template, redirect, make_response, request, flash
from flask import session as login_session

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, StockList, IndustryList, User, Portfolio, Bracket

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

# Default location - currently lists industries
@app.route('/')
def showSectors():
    if 'handle' not in login_session:
       return redirect( '/login' )
    inds =  session.query(IndustryList).all() 
    return render_template( 'sector_info.html', industries = inds, website = host )

# Called to get a suer to login in
@app.route('/login')
def showLogin():
    # Create a state token to prevent forgery
    # Store it in the session for later validation.
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    app.logger.info('login_session[state] is %s', login_session['state'] )
    return render_template('login.html', STATE=state )

# Called when sector is clicked - temporary 
@app.route('/sector/<string:sector_name>/')
def printSector(sector_name): 
    if 'handle' not in login_session:
       return redirect( '/login' )
    sector_name = sector_name.replace( '_', ' ')
    stock_list = session.query(StockList).filter(StockList.sector==sector_name)
    print sector_name.replace('_',' ' )
    return render_template( 'stock_info.html', stocks = stock_list, sector_name=sector_name.replace('_',' ' ) )

# Method called to set a user's bracket entry
@app.route('/set_bracket', methods=['POST'])
def setBracket():
    winner_1a = request.form.get('bracket-round1A')
    winner_1b = request.form.get('bracket-round1B')
    winner_2 = request.form.get('bracket-round2')

    images = ( 'static/images/mcd.png', 'static/images/sonc.jpg', 'static/images/bbry.jpg', 'static/images/nok.jpg' );

    updateBracket(login_session, (winner_1a, winner_1b, winner_2))
    
    brackets = getBrackets(); 
    return render_template( 'show_brackets.html', bracket_list = brackets, symbol_image=images ) 
   
    

# Method called from the client AJAX to determine if handle is unique
@app.route('/verifyHandleUniqueness', methods=['POST'])
def verifyHandleUniqueness():

    if session.query(User).filter_by( site_handle = request.args.get('handle')).count() == 0 :
      return_val = 'unique'
    else:
      app.logger.info('verifyHandleUniqueness() : name %s is NOT unique  '%  request.args.get('handle')  )
      return_val = 'not_unique'

    return json.dumps({'return_value': return_val})

# Called from submit to create account after unique handle is entered
@app.route('/setup_account', methods=['POST'])
def setupAccount():
  
    app.logger.info('setupAccount() : name is %s' % request.form['handle_name'] )

    if request.args.get('state') != login_session['state']:
        return render_template('poo.html')

    login_session['handle'] =  request.form['handle_name']
    createUser(login_session);
    return redirect( '/' )

@app.route('/bracket')
def showBracket():
   return render_template( 'bracket.html' )
    
@app.route('/catClicker')
def catClicker():
   return render_template( 'cat_clicker.html' )
    

#########################
# User id centric methods
#########################
def updateBracket(login_session, picks):

    current_user_id = getUserID( login_session['email'] )

    if session.query(Bracket).filter(Bracket.user_id == current_user_id ).count() == 0:
        bracket = Bracket( user_id = current_user_id,   \
                           bracket_1A_winner = picks[0],\
                           bracket_1B_winner = picks[1],\
                           bracket_2_winner = picks[2] )
    else:
         bracket = session.query(Bracket).filter(Bracket.user_id==current_user_id).one()
         bracket.bracket_1A_winner = picks[0]
         bracket.bracket_1B_winner = picks[1]
         bracket.bracket_2_winner = picks[2] 

    session.add( bracket )
    session.commit()

def getBrackets():
    brackets = session.query(Bracket).join(User).all()
    return brackets


def createUser(login_session):

    newUser = User( site_handle = login_session['handle'],  \
                    email = login_session['email'] )
                    #provider = login_session['provider'] )

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
#########################
# END User id centric methods
#########################
   

#######################################
#  BEGIN CONNECT/LOGIN
#######################################
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    #app_secret = json.loads( open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    #app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']

    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % ( app_id, app_secret, access_token) 
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']
    login_session['username'] = data['name']
    login_session['provider'] = 'facebook' 

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    
    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if user_id is None :
       response = make_response(json.dumps({'status':'OK','handle':'None'}), 200 )
    else:
       user = getUserInfo(user_id)
       login_session['handle'] =  user.site_handle
       response = make_response(json.dumps({'status':'OK','handle':user.site_handle}), 200 )
    return response
### END fbconnect



@app.route('/gconnect', methods=['POST'])
def gconnect():
    app.logger.info("gconnect")
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
    login_session['provider'] = 'google'

    #app.logger.info("user :  %s, pic : %s, email : %s, provider : %s" % (data['name'], data['picture'],  data['email'],  login_session['provider']) )
    app.logger.info("user :  %s," % data['name'] );

    user_id = getUserID(login_session['email'])

    app.logger.info("user_id  :  %s ", user_id );

    if user_id is None :
       response = make_response(json.dumps({'status':'OK','handle':'None'}), 200 )
    else:
       user = getUserInfo(user_id)
       login_session['handle'] =  user.site_handle
       response = make_response(json.dumps({'status':'OK','handle':user.site_handle}), 200 )
    return response
#######################################
#  END CONNECT/LOGIN
#######################################



#######################################
#  BEGIN DISCONNECT  
#######################################
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]

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

@app.route('/disconnect')
def disconnect( ):
    if login_session['provider'] == 'google':
       gdisconnect()
    if login_session['provider'] == 'facebook':
       fbdisconnect()

    login_session.clear()

    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
#######################################
#  END DISCONNECT  
#######################################






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


