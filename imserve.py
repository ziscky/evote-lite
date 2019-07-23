from flask import Flask
from flask import request
import simplejson as json
import os.path
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

workdir = os.path.dirname(os.path.realpath(__file__)) + "/"


def format_resp(data, success):
    obj = {
        "success": success,
        "message": data,
    }
    return json.dumps(obj)


def save(img):
    imghash = hashlib.md5(img).hexdigest()
    with open(workdir + imghash, "wb") as dataf:
        dataf.write(img)
        return imghash


def get(_hash):
    with open(workdir + _hash, "r") as dataf:
        data = dataf.read()
        # print("HERE",data)
        return data


@app.route('/upload', methods=['POST'])
def upload():
    img = request.get_data()
    hash = save(img)
    return hash


@app.route('/img/<hash>', methods=['GET'])
def _get(hash):
    return get(hash)


app.run(port=9000, host="0.0.0.0")
