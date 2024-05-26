from . import *
from .PeTemplates import *
from flask import Flask, jsonify, request, make_response,jsonify
from .GameMaster import GameMaster
from werkzeug.serving import run_simple

import threading
import json
import uuid
    
class CustomThread(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self._stop_event = threading.Event()
        self.app = app

    def run(self):
        while not self._stop_event.is_set():
            print('Thread is running...')
            self.app.GM.ResetGame(self.app.uselang)
            self.app.GM.RunGame()
            self.app.GM.EndGame()
            time.sleep(1)
            self.stop()
            self.app.sessionId = None
            self.app.GM.exit_flag = True

    def stop(self):
        self._stop_event.set()
        
def ReturnJson(data):
    json_str = json.dumps(data, ensure_ascii=False).encode('utf-8')
    return json_str, 200, {"Content-Type":"application/json"}

def generateShortUuid():
    return uuid.uuid4().hex[:8]

app = Flask(__name__)
app.uselang = "en"

@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

@app.route('/')
def hello_world():
    return 'hello, world'

@app.route('/startGame')
def start_game():
    if app.GMrunning:
        return app.sessionId

    uselang=request.args["lang"]
    
    app.GMrunning = True
    app.uselang = "en" if uselang == "en" else "cn"
    app.sessionId = generateShortUuid()
    app.server_thread = CustomThread(app)
    app.server_thread.start()
    return {"sessionid": app.sessionId}

@app.route('/stopGame')
def stop_game():
    app.GMrunning = False
    if hasattr(app, 'server_thread'):
        app.server_thread.stop()
    app.sessionId = None
    app.GM.exit_flag = True
    return {"data": "OK"}

@app.route('/resetGame')
def reset_game():
    app.GMrunning = False
    if hasattr(app, 'server_thread'):
        app.server_thread.stop()
    app.sessionId = None
    app.GM.exit_flag = True
    return {"data": "OK"}

@app.route('/getMsg')
def get_msg():
    # app.GM.GetMessages()
    data = app.GM.GetMessages()
    return ReturnJson(data)

@app.route('/getPlayer')
def get_player():
    data = app.GM.GetPlayerInfo()
    return ReturnJson(data)

@app.route('/getVotes')
def get_vote():
    data = app.GM.GetVotes()
    return ReturnJson(data)

@app.route('/fakeEnding')
def def_fakeEnding():
    data = app.GM.FakeEnding()
    return ReturnJson(data)

@singleton
class GameServer(object):
    
    def __init__(self, round=20, qsize=3):
        self.GM = GameMaster(round, qsize, False)
        app.GM = self.GM
        app.GMrunning = False
        pass

    def Run(self, host="localhost", port="8000"):
        run_simple(host, port, app)


# if __name__ == '__main__':
#     app.run()


