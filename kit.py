from flask import Flask
from flask import request
import simplejson as json
import os.path
from flask_cors import CORS
from evotepy import Litenode,Identity
import time

app = Flask(__name__)
CORS(app)


workdir  = os.path.dirname(os.path.realpath(__file__))+"/"
dht_config = ""
id = ""
nodes = ""


def format_resp(data, success):
    obj = {
        "success": success,
        "message": data,
    }
    return json.dumps(obj)


@app.route('/svlogin', methods=['POST'])
def svlogin():
    fprint = request.form.get('password')

    #get genesis block
    genesis = node.GetBlock(0,"PARENT")
    if len(genesis) == 0:
        print("Not received Genesis block yet")
        return format_resp("Not ready",0)

    # seed pub/priv key
    #check if derived pubkey matches the recorded one

    keys = node.SeedKeys(fprint)
    parsed_keys = json.loads(keys)

    iespub = parsed_keys["e_private_key"]
    iespriv = parsed_keys["e_public_key"]

    #get sv pk from genesis block

    parsed_genesis = json.loads(genesis)

    supervisors = parsed_genesis["Supervisors"]
    for supervisor in supervisors:
        if supervisor["PublicKey"] == iespub:
            return format_resp(iespub,1)
    return format_resp("Invalid Credentials",0)

node = Litenode(workdir+dht_config,workdir+id)
node.AddKnownNodes(workdir+nodes)
node.Start()

#cache genesis block
node.GetBlock(0,"PARENT")

