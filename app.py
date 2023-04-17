from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS, cross_origin
import time
from gpt3 import create_embeddings, QAchain

def get_script_response(bot_id, bot_name, base_url):
    script_response = """
        <button id="chat-button" onclick="open_chatbox()"></button>
        <iframe src="CHATBOT_WIDGET_URL" id="chat-widget" </iframe>
        <script>
            window.gpt_chatbot = {
                id:"CHATBOT_ID",
                name:"CHATBOT_NAME",
                ask_url:"CHATBOT_ASK_URL"
            }
            function open_chatbox(){
                console.log("Open Chatbox");
            }
        </script>
    """
    script_response = script_response.replace("CHATBOT_ID",bot_id)
    script_response = script_response.replace("CHATBOT_NAME", bot_name)
    script_response = script_response.replace("CHATBOT_WIDGET_URL", f'{base_url}bot/')
    script_response = script_response.replace("CHATBOT_ASK_URL", f'{base_url}bot/ask/')
    return script_response

running_chains = dict()

app = Flask(__name__)
CORS(app)

client = MongoClient('mongodb://localhost:27017/')
db = client.gpt_chatbot

@app.route('/')
def index():
    return render_template('index.html', script_result="") 

@app.route('/newbot', methods=['POST'])
def generate_new_bot():
    bot_name = request.form['name']
    sitemap_url = request.form['url']
    domain_name = request.form['domain']
    
    namespace = create_embeddings(sitemap_url, domain_name)

    new_bot = {
        'name': bot_name,
        'sitemap_url': sitemap_url,
        'domain_name': domain_name,
        'namespace': namespace 
    }
    result = db.chatbots.insert_one(new_bot)
    return get_script_response(str(result.inserted_id), bot_name, request.host_url)

@app.route('/bot/start', methods=['GET'])
def start_chatbot():
    bot_id = request.args.get('id')
    bot = db.chatbots.find_one({'_id': ObjectId(bot_id)})
    namespace = bot['namespace']
    new_qa_chain = QAchain(namespace)
    qa_chain_id = bot_id + str(round(time.time()*1000))
    running_chains[qa_chain_id] = new_qa_chain
    return {
        'qa_chain_id': qa_chain_id
    }

@app.route('/bot/close', methods=['GET'])
def close_chatbot():
    qa_chain_id = request.args.get('id')
    running_chains.pop(qa_chain_id)
    return "QA Chain Closed"

@app.route('/bot/ask', methods=['POST'])
def ask_chatbot():
    qa_chain_id = request.json['qa_chain_id']
    qn = request.json['question']
    qa_chain = running_chains[qa_chain_id]
    ans = qa_chain.ask(qn)
    return {
        'answer': ans
    }

if __name__ == "__main__":
    app.run(debug=True)