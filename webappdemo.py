from flask import Flask, Response, request, render_template, jsonify
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
import werkzeug
from werkzeug.serving import run_with_reloader
from socketio.server import SocketIOServer
from gevent import monkey
from string import punctuation
import tweepy
import flask
import json
from tweepy.models import JSONModel
import sys
import gspread

monkey.patch_all()


app = Flask(__name__)
app.debug = True

CONSUMER_TOKEN='***************************************'
CONSUMER_SECRET='****************************************'
CALLBACK_URL = 'http://localhost:6020/verify'

session = dict()
api=object
stream = object
auth=object


@app.route("/")
def send_token():
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN,
        CONSUMER_SECRET,
        CALLBACK_URL)
 
    try:
        #get the request tokens
        redirect_url= auth.get_authorization_url()
        session['request_token']= (auth.request_token.key,
        auth.request_token.secret)
    except tweepy.TweepError:
        print 'Error! Failed to get request token'
 
    #this is twitter's url for authentication
    return flask.redirect(redirect_url) 
 
@app.route("/verify")
def get_verification():
 
    #get the verifier key from the request url
    verifier= request.args['oauth_verifier']
    global auth
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    token = session['request_token']
    del session['request_token']
     
    auth.set_request_token(token[0], token[1])
    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        print 'Error! Failed to get access token.'
    global api
    api = tweepy.API(auth)
    
    return flask.redirect(flask.url_for('start'))

#tweepy stream 
class StdOutListener(tweepy.StreamListener):
    def on_status(self, status):
        tel = {'name':status.user.name,'profile_image_url':status.user.profile_image_url,'text':status.text}
        TweetsNamespace.broadcast('tweet_text', json.dumps(tel))
        print '\n %s' % (status.text.encode('ascii', 'replace'))
    def on_error(self, status_code):
        print >> sys.stderr, 'Encountered error with status code:', status_code
        return True 

    def on_timeout(self):
        print >> sys.stderr, 'Timeout...'
        return True 

@app.route("/start")
def start():
    #auth done
    global stream
    stream = tweepy.streaming.Stream(auth, StdOutListener())
    stream.filter(track=['#facebook'],async=True)    
     
    return flask.render_template('main.html')



class TweetsNamespace(BaseNamespace):
    sockets = {}

    def recv_connect(self):
        print "Got a socket connection" # debug
        self.sockets[id(self)] = self

    def disconnect(self, *args, **kwargs):
        print "Got a socket disconnection" # debug
        if id(self) in self.sockets:
            del self.sockets[id(self)]

        super(TweetsNamespace, self).disconnect(*args, **kwargs)
    # broadcast to all sockets on this channel!

    @classmethod
    def broadcast(self, event, message):
        for ws in self.sockets.values():
            ws.emit(event, message)

#Hashtag search
@app.route('/hashtag/<qstring>')
def setqstring(qstring):
    query = qstring
    global stream
    stream.disconnect()
    stream.filter(track=[query],async=True)
    return ''

#Listening to web socket
@app.route('/socket.io/<path:rest>')
def push_stream(rest):
    try:
        socketio_manage(request.environ, {'/tweets': TweetsNamespace}, request)
        return ''
    except:
        app.logger.error("Exception while handling socketio connection", exc_info=True)


@werkzeug.serving.run_with_reloader
def run_dev_server():
    app.debug = True
    port = 6020
    SocketIOServer(('', port), app, resource="socket.io").serve_forever()

if __name__ == "__main__":
    run_dev_server()
