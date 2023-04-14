from flask import Flask, render_template, request
from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId

from gpt import create_embeddings, QAchain

script_response = """
    <script>
        window.gpt_chatbot_id={}
    </script>
    <iframe src="https://localhost:5000/bot" id="chat-widget" </iframe>
"""

running_chains = dict()

app = Flask(__name__)

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
    return script_response.format(result.inserted_id)

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
    qn = request.form['question']
    qa_chain = running_chains[bot_id]
    ans = qa_chain.ask(qn)
    return ans['answer']

if __name__ == "__main__":
    app.run(debug=True)