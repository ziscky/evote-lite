from flask import Flask
from flask import request
import simplejson as json
import os.path
from flask_cors import CORS
from evotepy import Litenode, Identity
import time

app = Flask(__name__)
CORS(app)

workdir = os.path.dirname(os.path.realpath(__file__)) + "/"
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


##Fingerprint Detect
@app.route('/fingerprint/detect', methods=['POST'])
def get_fingerprint():
    ##TODO: read fingerprint from sensor
    return format_resp("FPRINTHASH", 1)


@app.route('/svlogin', methods=['POST'])
def svlogin():
    fprint = request.form.get('password')

    # get genesis block
    genesis = node.GetBlock(0, "PARENT")
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


@app.route('/voter/vote', methods=['POST'])
def vote():
    name = request.form.get('fName')
    idNo = request.form.get('idNo')
    gender = request.form.get('gender')
    fprint = request.form.get('fPrint')
    photo = request.form.get('file')

    # derive keys from fprint
    keys = node.SeedKeys(fprint, True)
    print(keys)
    parsed_keys = json.loads(keys)
    print(parsed_keys)

    # sign Name,IdNumber and photo
    identity = Identity(parsed_keys["public_key"], parsed_keys["private_key"], parsed_keys["e_public_key"],
                        parsed_keys["e_private_key"])

    data = {
        "Name": name,
        "IdNumber": idNo,
        "Gender": gender,
        "photo": photo,
    }
    ##create transaction and broadcast to block chain
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
    fprint = request.form.get('password')

    keys = node.SeedKeys(fprint, True)
    print(keys)
    parsed_keys = json.loads(keys)
    print(parsed_keys)
    identity = Identity(parsed_keys["public_key"], parsed_keys["private_key"], parsed_keys["e_public_key"],
                        parsed_keys["e_private_key"])

    transactions = node.GetTransaction(identity.DSAPublicKey(), "PARENT")

    if transactions == "":
        return format_resp("Waiting for block chain confirmation", -1)

    print(transactions)
    parsed_transactions = json.loads(transactions)
    voters = []
    data = parsed_transactions["transactions"]
    if data == "ERROR":
        return format_resp("Not regoistered on block chain", -2)

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


@app.route('/close/vote', methods=['GET'])
def fork():
    node.CloseChain()
    return format_resp("success", 1)


@app.route('/demob', methods=['GET'])
def demob():
    # demo
    node.GetBlock(0, "PARENT")


node = Litenode(workdir + dht_config, workdir + id)
node.AddKnownNodes(workdir + nodes)
node.Start()
# demo()

# cache genesis block
node.GetBlock(0, "PARENT")

app.run(port=7777)
