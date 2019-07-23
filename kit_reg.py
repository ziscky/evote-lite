from flask import Flask
from flask import request
import simplejson as json
import os.path
import requests
from flask_cors import CORS
from evotepy import Litenode, Identity
from biometric.Bio import Bio
import time

app = Flask(__name__)
CORS(app)

workdir = os.path.dirname(os.path.realpath(__file__)) + "/"
imgserver = "http://localhost:9000"
dht_config = "conf3.json"
id = "id3.json"
nodes = "nodes.json"

accepted_transactions = {}


def format_resp(data, success):
    obj = {
        "success": success,
        "message": data,
    }
    return json.dumps(obj)


# Fingerprint Detect
@app.route('/fingerprint/detect', methods=['POST'])
def get_fingerprint():
    hash = fprintHelper.requestFPrint()
    if hash == "ERROR":
        return format_resp("Error. Try Again", 0)
    return format_resp(hash, 1)


@app.route('/svlogin', methods=['POST'])
def svlogin():
    fprint = request.form.get('password')

    # get genesis block
    genesis = node.GetBlock(0, "PARENT", False)
    if len(genesis) == 0:
        print("Not received Genesis block yet")
        return format_resp("Not ready", 0)

    parsed_genesis = json.loads(genesis)
    tx_hash = parsed_genesis["tx_hashes"][0]

    print(tx_hash)

    transaction = parsed_genesis["transactions"][tx_hash]
    parsed_transaction = json.loads(transaction)

    supervisors = json.loads(parsed_transaction["data"])["Supervisors"]
    print(supervisors)
    # supervisors = parsed_transaction["Supervisors"]
    for supervisor in supervisors:
        if supervisor["Fingerprint"] == fprint:
            return format_resp("Success", 1)
    return format_resp("Invalid Credentials", 0)


@app.route('/voter/register', methods=['POST'])
def register_voter():
    name = request.form.get('fName')
    idNo = request.form.get('idNo')
    gender = request.form.get('gender')
    fprint = request.form.get('fPrint')
    photo = request.form.get('file')

    # derive keys from fprint
    keys = node.SeedKeys(idNo, True)
    print(keys)
    parsed_keys = json.loads(keys)
    print(parsed_keys)

    resp = requests.post(imgserver + "/upload", photo)
    photo_hash = resp.text

    # sign Name,IdNumber and photo
    identity = Identity(parsed_keys["public_key"], parsed_keys["private_key"], parsed_keys["e_public_key"],
                        parsed_keys["e_private_key"])

    data = {
        "Name": name,
        "IdNumber": idNo,
        "Gender": gender,
        "photo": photo_hash,
    }
    # create transaction and broadcast to block chain
    signature = identity.Sign(json.dumps(data))

    print(signature)

    payload = {
        "data": json.dumps(data),
        "timestamp": time.time(),
        "pk": identity.DSAPublicKey(),
        "signature": signature
    }

    node.BroadcastTransaction(json.dumps(payload))

    return format_resp("success", 1)


@app.route('/voter/get', methods=['POST'])
def get_voters():
    transactions = node.GetTransactions()

    parsed_transactions = json.loads(transactions)
    voters = []
    for transaction in parsed_transactions["transactions"]:
        tx = json.loads(transaction)
        data = tx["data"]
        print(json.loads(data.replace("\'", "\"")))
        data = json.loads(data.replace("\'", "\""))
        parsed = {
            "fName": data["Name"],
            "idNo": data["IdNumber"],
            "gender": data["Gender"],
            "photo": data["photo"]
        }
        print(parsed)
        voters.append(parsed)

    return format_resp(voters, 1)


@app.route('/voter/check', methods=['POST'])
def get_voter():
    fprint = request.form.get('fprint')
    idNo = request.form.get('idNo')

    keys = node.SeedKeys(fprint, True)
    print(keys)
    parsed_keys = json.loads(keys)
    print(parsed_keys)
    identity = Identity(parsed_keys["public_key"], parsed_keys["private_key"], parsed_keys["e_public_key"],
                        parsed_keys["e_private_key"])

    transactions = node.GetTransaction(identity.DSAPublicKey(), "PARENT")

    if transactions == "":
        return format_resp("Waiting for block chain confirmation", -1)

    print("119-->", transactions)
    parsed_transactions = json.loads(transactions)
    voters = []
    data = parsed_transactions["transaction"]
    if data == "ERROR":
        return format_resp("Not registered on block chain", -2)

    data = json.loads(parsed_transactions["transaction"])
    print(data)
    parsed = {
        "fName": data["Name"],
        "idNo": data["IdNumber"],
        "gender": data["Gender"],
        "photo": data["photo"]
    }
    print(parsed)
    voters.append(parsed)

    return format_resp(voters, 1)


@app.route('/election/get', methods=['POST'])
def get_election():
    # get genesis block
    genesis = node.GetBlock(0, "PARENT",False)
    if len(genesis) == 0:
        print("Not received Genesis block yet")
        return format_resp("Not ready", 0)

    parsed_genesis = json.loads(genesis)
    tx_hash = parsed_genesis["tx_hashes"][0]

    print(tx_hash)

    transaction = parsed_genesis["transactions"][tx_hash]
    parsed_transaction = json.loads(transaction)

    posts = json.loads(parsed_transaction["data"])["Posts"]
    print(posts)

    for post in posts:
        i = 0
        for candidate in post["Candidates"]:
            candidate["Id"] = i
            tmp = candidate["Photo"]
            resp = requests.get(imgserver+"/img/"+tmp)
            candidate["Photo"] = resp.text
            i += 1
    print(posts)
    return format_resp(posts, 1)


@app.route('/voter/vote', methods=['POST'])
def cast_vote():
    vote = request.form.get('vote')
    fprint = request.form.get('fprint')
    idNo = request.form.get('idNo')

    print(vote)
    print(fprint)
    parsed_vote = json.loads(vote)

    choices = []
    for choice in parsed_vote:
        data = {
            "Name": choice["Name"],
            "Party": choice["Party"],
            "Post": choice["Post"]
        }
        choices.append(data)

    # derive keys from fprint
    keys = node.SeedKeys(idNo, True)
    print(keys)
    parsed_keys = json.loads(keys)
    print(parsed_keys)

    # sign Name,IdNumber and photo
    identity = Identity(parsed_keys["public_key"], parsed_keys["private_key"], parsed_keys["e_public_key"],
                        parsed_keys["e_private_key"])

    #create transaction and broadcast to block chain
    signature = identity.Sign(json.dumps(choices))

    print(signature)

    payload = {
        "data": json.dumps(choices),
        "timestamp": time.time(),
        "pk": identity.DSAPublicKey(),
        "signature": signature
    }

    node.BroadcastTransaction(json.dumps(payload))

    return format_resp("success", 1)


@app.route('/close/vote', methods=['GET'])
def close_chain():
    node.CloseChain()
    return format_resp("success", 1)


@app.route('/fork/vote', methods=['GET'])
def fork():
    node.InitFork()
    return format_resp("success", 1)


@app.route('/init', methods=['POST'])
def demo():
    # demo
    print("INIT>>>>>", request.get_data())
    data = {
        "timestamp": time.time(),
        "data": request.get_data()
    }
    node.InitChain(json.dumps(data))
    return format_resp("success", 1)


@app.route('/demob', methods=['GET'])
def demob():
    # demo
    node.GetBlock(0, "PARENT")


fprintHelper = Bio(workdir)

node = Litenode(workdir + dht_config, workdir + id)
node.AddKnownNodes(workdir + nodes)
node.Start(False)
# demo()

# cache genesis block
# node.GetBlock(0, "PARENT", False)

app.run(port=7778, host="0.0.0.0")
