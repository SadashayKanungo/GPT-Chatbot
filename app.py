from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId
from flask_cors import CORS, cross_origin
from gpt import create_embeddings, QAchain

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
    script_response = script_response.replace("CHATBOT_ASK_URL", f'{base_url}bot/ask?id={bot_id}/')
    return script_response

running_chains = dict()

app = Flask(__name__)
CORS(app)

client = MongoClient('mongodb://localhost:27017/')
db = client.gpt_chatbot
fs = gridfs.GridFS(db)

@app.route('/')
def index():
    return render_template('index.html', script_result="") 

@app.route('/newbot', methods=['POST'])
def generate_new_bot():
    bot_name = request.form['name']
    sitemap_url = request.form['url']
    domain_name = request.form['domain']
    
    pkl_data = create_embeddings(sitemap_url, domain_name)
    pkl_id = fs.put(pkl_data)
    print("Saved PKL File, id: ", pkl_id)
    new_bot = {
        'name': bot_name,
        'sitemap_url': sitemap_url,
        'domain_name': domain_name,
        'pkl_id': pkl_id 
    }
    result = db.chatbots.insert_one(new_bot)
    return get_script_response(str(result.inserted_id), bot_name, request.host_url)

@app.route('/bot/start', methods=['GET'])
def start_chatbot():
    bot_id = request.args.get('id')
    bot = db.chatbots.find_one({'_id': ObjectId(bot_id)})
    pkl_id = bot['pkl_id']
    pkl_data = fs.get(pkl_id).read()
    print("Retrieved PKL File, id: ", pkl_id)
    new_qa_chain = QAchain(pkl_data)
    running_chains[bot_id] = new_qa_chain
    return "QA Chain Started"

@app.route('/bot/close', methods=['GET'])
def close_chatbot():
    bot_id = request.args.get('id')
    running_chains.pop(bot_id)
    return "QA Chain Closed"

@app.route('/bot/ask', methods=['POST'])
def ask_chatbot():
    bot_id = request.args.get('id')
    qn = request.json['question']
    qa_chain = running_chains[bot_id]
    ans = qa_chain.ask(qn)
    return {
        'answer': ans['answer']
    }

if __name__ == "__main__":
    app.run(debug=True)