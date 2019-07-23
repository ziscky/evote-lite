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
dht_config = "conf3.1.json"
id = "id3.json"
nodes = "nodes.json"

accepted_transactions = {}


def format_resp(data, success):
    obj = {
        "success": success,
        "message": data,
    }
    return json.dumps(obj)


@app.route('/explore/<height>', methods=['GET'])
def get_block(height):
    # get genesis block
    block = node.GetBlock(int(height), "PARENT", True)
    if len(block) == 0:
        print("Not received Genesis block yet")
        return format_resp("Not ready", 0)

    parsed_block = json.loads(block)
    print(parsed_block)

    return format_resp(parsed_block, 1)


@app.route('/explore', methods=['GET'])
def explore():
    # get genesis block
    i = 0
    blocks = []
    while True:
        block = node.GetBlock(i, "PARENT", True)
        if block == "":
            break
        blocks.append(json.loads(block))
        i += 1

    return format_resp(blocks, 1)


node = Litenode(workdir + dht_config, workdir + id)
node.AddKnownNodes(workdir + nodes)
node.Start(True)
# demo()

# cache genesis block
node.GetBlock(0, "PARENT", True)

app.run(port=5000, host="0.0.0.0")
