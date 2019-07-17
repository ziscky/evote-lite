from flask import Flask
from flask import request
import simplejson as json
import os.path
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)


workdir  = os.path.dirname(os.path.realpath(__file__))+"/"


def format_resp(data, success):
    obj = {
        "success": success,
        "message": data,
    }
    return json.dumps(obj)


def valid_key(pubkey):
    return os.path.isfile(workdir+pubkey)


def save(pubkey, data):
    with open(workdir+pubkey, "w+") as dataf:
        dataf.write(json.dumps(data,indent=4*' '))
        return
    print("ERROR SAVING FILE")


def load(pubkey):
    with open(workdir+pubkey, "r") as dataf:
        data = dataf.read()
        return data
    pass


@app.route('/generate', methods=['POST'])
def seed():
    seed = request.form.get('seed')
    # seed pub/priv key
    pub = "pubkey"
    priv = "privkey"
    try:
        storage = open(workdir+pub, "x")
        storage.close()
    except:
        pass

    return format_resp(pub, 1)


@app.route('/login', methods=['POST'])
def login():
    passw = request.form.get('password')

    # seed pub/priv key
    pub = "pubkey"
    storage = open(workdir+pub, "w+")
    storage.close()

    return format_resp(pub, 1)



##Election routes
@app.route('/election/create', methods=['POST'])
def create_election():
    name = request.form.get('name')
    uid = request.form.get('uid')

    if not valid_key(uid):
        return format_resp("success", -1)

    data = {
        "ID": 1,
        "ElectionName": name,
        "Created": time.time(),
        "Posts":[],
        "Supervisors":[]
    }

    save(uid, data)
    return format_resp("success", 1)


@app.route('/election/get', methods=['POST'])
def get_elections():
    uid = request.form.get('uid')
    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)

    numCandidates = 0
    for p in parsed["Posts"]:
        numCandidates += len(p["Candidates"])

    parsed["NumCandidates"] = numCandidates
    parsed["NumPosts"] = len(parsed["Posts"])
    return format_resp(json.dumps(parsed), 1)


##Post routes
@app.route('/post/create', methods=['POST'])
def create_post():
    name = request.form.get('name')
    uid = request.form.get('uid')

    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)
    app = {
        "Name": name,
        "Candidates": [],
    }

    parsed["Posts"].append(app)
    save(uid,parsed)

    return format_resp("success", 1)


@app.route('/post/get', methods=['POST'])
def get_posts():
    uid = request.form.get('uid')
    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)
    for post in parsed["Posts"]:
        post["NumCandidates"] = len(post["Candidates"])

    return format_resp(parsed["Posts"], 1)


@app.route('/candidate/create', methods=['POST'])
def create_candidate():
    uid = request.form.get('uid')
    name = request.form.get('name')
    gender = request.form.get('gender')
    party = request.form.get('party')
    slogan = request.form.get('slogan')
    photo = request.form.get('file')
    post = request.form.get('post')

    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)
    app = {
        "Name": name,
        "Gender": gender,
        "Party": party,
        "Slogan": slogan,
        "Photo": photo,
    }
    for p in parsed["Posts"]:
        if p["Name"] == post:
            print(p)
            p["Candidates"].append(app)

    save(uid,parsed)

    return format_resp("success", 1)


##Candidate routes


@app.route('/candidate/get', methods=['POST', 'GET'])
def get_candidates():
    uid = request.form.get('uid')
    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)
    selected = []
    for post in parsed["Posts"]:
        for candidate in post["Candidates"]:
            candidate["Post"] = post["Name"]
            selected.append(candidate)

    return format_resp(selected, 1)


##Supervisor routes
@app.route('/user/create', methods=['POST'])
def create_supervisor():
    uid = request.form.get('uid')
    name = request.form.get('fname')
    email = request.form.get('email')
    phoneNumber = request.form.get('phoneNumber')
    fprint = request.form.get('fprint')

    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)

    app = {
        "FName": name,
        "Email": email,
        "PhoneNumber": phoneNumber,
        "Fingerprint": fprint,
        "Kit":{},
    }

    parsed["Supervisors"].append(app)
    save(uid,parsed)

    return format_resp("success", 1)


@app.route('/user/get', methods=['POST'])
def get_supervisors():
    uid = request.form.get('uid')
    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)
    return format_resp(parsed["Supervisors"], 1)


##VotingKit routes
@app.route('/kit/create', methods=['POST'])
def create_kits():
    uid = request.form.get('uid')
    supervisor = request.form.get('supervisor')
    imei = request.form.get('imei')

    data = load(uid)
    parsed = json.loads(data)

    if not valid_key(uid):
        return format_resp("success", -1)

    pub = "svpubk"
    priv = "svprivk"

    app = {
        "Supervisor": supervisor,
        "IMEI": imei,
        "PublicKey": pub,
        "PrivateKey": priv,
    }
    for sv in parsed["Supervisors"]:
        if sv["FName"] == supervisor:
            sv["Kit"] = app

    save(uid,parsed)

    return format_resp("success", 1)


@app.route('/kit/get', methods=['POST'])
def get_kits():
    uid = request.form.get('uid')
    if not valid_key(uid):
        return format_resp("success", -1)

    data = load(uid)
    parsed = json.loads(data)
    kits = []
    for sv in parsed["Supervisors"]:
        if len(sv["Kit"]) == 0:
            continue
        kits.append(sv["Kit"])

    return format_resp(kits, 1)


##Fingerprint Detect
@app.route('/fingerprint/detect', methods=['POST'])
def get_fingerprint():
    ##TODO: read fingerprint from sensor
    return format_resp("FPRINTHASH", 1)


app.run(port=7777)
