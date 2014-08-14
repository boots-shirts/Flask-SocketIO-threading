#!/usr/bin/env python
import os
import time
import random
import json
from flask import Flask, Response, redirect, url_for, session, request,jsonify, render_template, copy_current_request_context
from flask_oauthlib.client import OAuth
from flask.ext.socketio import SocketIO, emit
import threading
import Queue

from gevent import monkey                        
monkey.patch_all()


                     
app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

myqueue=Queue.Queue(0)


oauth = OAuth(app)
douban = oauth.remote_app(
    #settings
)


@app.route('/')                                                   
def index():
    if 'douban_token' in session:
        return redirect(url_for('home'))  
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return douban.authorize(callback=url_for('authorized', _external=True))


@app.route('/login/authorized')
@douban.authorized_handler
def authorized(resp):
    #in summary, get token and store it in session
    return redirect(url_for('index'))                           

@douban.tokengetter
def get_douban_oauth_token():
    return session.get('douban_token')



class bg(threading.Thread):                                   #background thread class
    def _init_(self):
        threading.Thread.__init__(self)
    def run(self):
        with app.text_request_context():                      # request context here?
            while True:
                data=get_data()                  
                new_data=json.loads(data.data)
                myqueue.put(new_data)
                socketio.emit('response',                    #never get this message!!!
                              {'data': 'miniblog updated'},
                               namespace='/_GET')
                time.sleep(20)
 
def get_data():                                                     
    resp=douban.request('shuo/v2/statuses/home_timeline?count=20')                                     
    data=jsonify(data=resp.data)
    return data
          

@app.route('/home')                                             #request context here?
def home():
    #with app.test_request_cotext():     #if enabled, getting error: flask object has no attribute 'test_request_context'
    t1=bg()
    t1.daemon=True
    t1.start()
    return render_template('home.html')
                     

            
@socketio.on('send data', namespace='/_GET')              
def sendData():
    emit('response',{'data':'getting data...'})
    d=myqueue.get()
    myqueue.task_done()                               # is it necessary?
    while len(d)>=3:
        n=random.randint(1,3)
        for i in range(n):
            emit('message',{'data':json.dumps(d.pop())})
            time.sleep(0.5)
        time.sleep(3)
    while len(d)!=0:
        emit ('message',{'data':json.dumps(d.pop())})
        time.sleep(2)
    emit('next')

    
    

@socketio.on('disconnect', namespace='/_GET')
def test_disconnect():
    print('Client disconnected') 


    

if __name__ == '__main__':
    socketio.run(app)
    

