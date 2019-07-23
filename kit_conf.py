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


@app.route('/voter/check', methods=['POST'])
def get_voter():
    fprint = request.form.get('fprint')

    keys = node.SeedKeys(fprint, True)
    print(keys)
    parsed_keys = json.loads(keys)
    print(parsed_keys)
    identity = Identity(parsed_keys["public_key"], parsed_keys["private_key"], parsed_keys["e_public_key"],
                        parsed_keys["e_private_key"])

    transactions = node.GetTransaction(identity.DSAPublicKey(), "PARENT")
    votes = node.GetTransaction(identity.DSAPublicKey(), "FORK")

    if transactions == "":
        return format_resp("Waiting for block chain confirmation", -1)

    if votes == "":
        return format_resp("Waiting for voting block confirmations", -1)

    print("55-->", transactions)
    print("56-->", votes)

    parsed_transactions = json.loads(transactions)
    parsed_votes = json.loads(votes)

    voters = []
    cast_votes = []

    data = parsed_transactions["transaction"]
    if data == "ERROR":
        return format_resp("Not registered on block chain", -2)

    data = json.loads(parsed_transactions["transaction"])
    parsed = {
        "fName": data["Name"],
        "idNo": data["IdNumber"],
        "gender": data["Gender"],
        "photo": data["photo"]
    }
    voters.append(parsed)

    data = json.loads(parsed_votes["transaction"])
    for v in data:
        cast_votes.append({
            "post": v["Post"],
            "party": v["Party"],
            "candidate": v["Name"],
        })

    resp = {
        "users": voters,
        "votes": cast_votes
    }

    print(resp)

    return format_resp(resp, 1)



node = Litenode(workdir + dht_config, workdir + id)
node.AddKnownNodes(workdir + nodes)
node.Start(False)
# demo()

# cache genesis block
node.GetBlock(0, "PARENT",False)

app.run(port=7779,host="0.0.0.0")
