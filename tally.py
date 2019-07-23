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


@app.route('/posts', methods=['GET'])
def posts():
    genesis = node.GetBlock(0, "PARENT", False)
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
    return format_resp(posts, 1)


@app.route('/votes', methods=['POST'])
def tally():
    selected_post = request.form.get("post")
    # get blocks
    blocks = explore()
    print("Found blocks: ", len(blocks))

    if len(blocks) == 0:
        print("Not received any blocks yet")
        return format_resp("Not ready", 0)

    results = {}
    i = -1
    for block in blocks:
        if block["type"] != "FORK":
            continue
        i += 1

        if i == 0:
            print("SKIPPING FORK INIT")
            continue

        for tx_hash in block["tx_hashes"]:
            transaction = block["transactions"][tx_hash]
            parsed_transaction = json.loads(transaction)

            votes = json.loads(parsed_transaction["data"])
            parsed_votes = json.loads(votes["data"])

            for parsed_vote in parsed_votes:
                if parsed_vote["Post"] not in results:
                    results[parsed_vote["Post"]] = {}

                if parsed_vote["Name"] in results[parsed_vote["Post"]]:
                    results[parsed_vote["Post"]][parsed_vote["Name"]]["count"] += 1
                else:
                    results[parsed_vote["Post"]][parsed_vote["Name"]] = {
                        "party": parsed_vote["Party"],
                        "count": 1
                    }

    print(results)

    if len(blocks) > 0:
        # get election data from genesis and fill in votes
        parsed_genesis = blocks[0]
        tx_hash = parsed_genesis["tx_hashes"][0]

        print("GENESIS->", tx_hash)

        transaction = parsed_genesis["transactions"][tx_hash]
        parsed_transaction = json.loads(transaction)

        posts = json.loads(parsed_transaction["data"])["Posts"]
        # print(posts)

        for post in posts:
            if post["Name"] not in results:
                results[post["Name"]] = {}
                for candidate in post["Candidates"]:
                    results[post["Name"]][candidate["Name"]] = {
                        "party": candidate["Party"],
                        "count": 0,
                    }
                continue

            for candidate in post["Candidates"]:
                if candidate["Name"] not in results[post["Name"]]:
                    results[post["Name"]][candidate["Name"]] = {
                        "party": candidate["Party"],
                        "count": 0,
                    }
    # format results
    parsed = format_results(results)
    print(parsed)

    payload = []
    for p in parsed:
        if p["post"] == selected_post:
            total = p["total"]
            for candidate in p["candidates"]:
                candidate["perc"] = (candidate["noVotes"]/total) * 100
                payload.append(candidate)

    return format_resp(payload, 1)


def format_results(results):
    parsed = []
    for key, val in results.items():
        postName = key
        total = 0
        candidates = []
        for ik, iv in val.items():
            candidateName = ik
            candidateParty = iv["party"]
            votes = iv["count"]
            total += votes
            candidates.append({
                "name": candidateName,
                "party": candidateParty,
                "noVotes": votes,
            })
        tmp = {
            "post": postName,
            "total": total,
            "candidates": candidates
        }
        parsed.append(tmp)
    return parsed


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

    return blocks


node = Litenode(workdir + dht_config, workdir + id)
node.AddKnownNodes(workdir + nodes)
node.Start(True)

node.GetBlock(0, "PARENT", True)

app.run(port=4000, host="0.0.0.0")
