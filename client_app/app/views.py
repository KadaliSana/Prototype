import datetime
import json

import requests
from flask import render_template, redirect, request

from app import app

CONNECTED_NODE_CHAIN_ADDRESS = "http://127.0.0.1:8000/chain"
CONNECTED_NODE_NEW_TX_ADDRESS = "http://127.0.0.1:8000/transactions/new"

posts = []


@app.route('/')
def index():
    return render_template('index.html',
                           title='Prototype ',
                           posts=posts)


@app.route('/submit', methods=['POST'])
def submit_textarea():

    post_content = request.form["body"]
    author = request.form["author"]

    print("Valid args receiveds")

    post_object = {
          'author': author,
          'body': post_content,
          'time': datetime.datetime.now().strftime('%H:%M')
    }


    res = requests.post(CONNECTED_NODE_NEW_TX_ADDRESS,
                        json=post_object,
                        headers={'Content-type': 'application/json'})

    if res.status_code == 201:
        print(res.text)

    return redirect('/fetch')

#FIXME: Develop a server_node endpoint for this.
@app.route('/fetch', methods=['POST', 'GET'])
def fetch_posts():
    resp = requests.get(CONNECTED_NODE_CHAIN_ADDRESS)
    if resp.status_code == 200:
        content = []
        chain = json.loads(resp.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                # Adding just for visiblity
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['server_timestamp'], reverse=True)

    else:
        print("Some Error ocurred while fetching the chain")

    return redirect('/')

'''
Sample chain response
{
  "chain": [
    {
      "index": 1, 
      "previous_hash": "1", 
      "proof": 100, 
      "timestamp": 1512904176.946647, 
      "transactions": []
    }, 
    {
      "index": 2, 
      "previous_hash": "a2728924c133546671e71cb9d9951f6e68b488deae483c2527f281b2a9e35491", 
      "proof": 35293, 
      "timestamp": 1512904218.593914, 
      "transactions": [
        {
          "author": "fsjklfjds", 
          "body": "Hello basdf", 
          "time": "16:40:18"
        }
      ]
    }
  ], 
  "length": 2
}
'''
