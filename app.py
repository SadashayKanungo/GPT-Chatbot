from flask import Flask, render_template, request, redirect, jsonify, make_response, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS, cross_origin
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, current_user, jwt_required, JWTManager, get_csrf_token
import uuid
import time
from gpt3 import create_embeddings, QAchain

running_chains = dict()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = b'\xcc^\x91\xea\x17-\xd0W\x03\xa7\xf8J0\xac8\xc5'
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60*60*24
app.config["JWT_CSRF_CHECK_FORM"] = True 
app.config["JWT_CSRF_IN_COOKIES"] = False 

app.config['CHATBOT_STATIC_PATH'] = 'chatbot/build'
app.config['CHATBOT_SCRIPT_DIR'] = 'cdn'
app.config['CHATBOT_SCRIPT_FILE'] = 'chatbot.js'

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app)

client = MongoClient('mongodb://localhost:27017/')
db = client.gpt_chatbot

# JWT and Login Helpers
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user['_id']

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    user = db.users.find_one({
        "_id": identity
    })
    return user

# User Routes
@app.route('/user/signup', methods=['POST'])
def signup():
    # Create the user object
    user = {
        "_id": uuid.uuid4().hex,
        "name": request.form.get('name'),
        "email": request.form.get('email'),
        "password": request.form.get('password'),
        "token": None
    }

    # Encrypt the password
    user['password'] = bcrypt.generate_password_hash(user['password'])

    # Check for existing email address
    if db.users.find_one({ "email": user['email'] }):
        return jsonify({ "error": "Email address already in use" }), 400
    
    # Grant Access Token
    access_token = create_access_token(identity=user)
    user["token"] = access_token
    
    # Add to Database
    if db.users.insert_one(user):
        response = make_response(jsonify(access_token=access_token))
        response.set_cookie('access_token_cookie', access_token, max_age=app.config["JWT_ACCESS_TOKEN_EXPIRES"])
        return response

    return jsonify({ "error": "Signup failed" }), 400

@app.route('/user/signout')
@jwt_required()
def signout():
    user = db.users.find_one_and_update({'_id':current_user['_id']}, {'$set': {'token': None}})
    response = make_response(redirect('/'))
    response.delete_cookie('access_token_cookie')
    return response

@app.route('/user/login', methods=['POST'])
def login():
    user = db.users.find_one({
        "email": request.form.get('email')
    })

    if user and bcrypt.check_password_hash(user['password'], request.form.get('password')):
        access_token = create_access_token(identity=user)
        user = db.users.find_one_and_update({'_id':user['_id']}, {'$set': {'token': access_token}})
        response = make_response(jsonify(access_token=access_token))
        response.set_cookie('access_token_cookie', access_token, max_age=app.config["JWT_ACCESS_TOKEN_EXPIRES"])
        return response

    return jsonify({ "error": "Invalid login credentials" }), 401

# Frontend and Static Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard/')
@jwt_required()
def dashboard():
    if not current_user['token']:
        return jsonify({ "error": "Not Authorized" }), 401

    bots = db.chatbots.find({'owner':current_user['_id']})
    return render_template('dashboard.html', user=current_user, bots=bots, csrf_token=get_csrf_token(current_user['token']))

@app.route('/bot/', defaults={'path': ''})
@app.route('/bot/<path:path>')
def serve(path):
    if path != "":
        return send_from_directory(app.config['CHATBOT_STATIC_PATH'], path, as_attachment=False)
    else:
        return send_from_directory(app.config['CHATBOT_STATIC_PATH'], 'index.html', as_attachment=False)

@app.route('/cdn/<path:filename>')
def get_script(filename):
    return send_from_directory(app.config['CHATBOT_SCRIPT_DIR'], filename, as_attachment=False)

# Bot Script Generation
def get_script_response(bot_id, base_url):
    script_response = '<script src="CHATBOT_SCRIPT_URL" id="CHATBOT_ID"></script>'
    script_response = script_response.replace("CHATBOT_ID",bot_id)
    script_file = app.config['CHATBOT_SCRIPT_FILE']
    script_response = script_response.replace("CHATBOT_SCRIPT_URL", f'{base_url}cdn/{script_file}')
    return script_response

# Bot Functioning Routes
@app.route('/newbot/', methods=['POST'])
@jwt_required()
def generate_new_bot():
    bot_name = request.form.get('name')
    sitemap_url = request.form.get('url')
    domain_name = request.form.get('domain')
    
    namespace = create_embeddings(sitemap_url, domain_name)

    new_bot = {
        '_id': uuid.uuid4().hex,
        'name': bot_name,
        'sitemap_url': sitemap_url,
        'domain_name': domain_name,
        'namespace': namespace,
        'owner': current_user['_id'],
    }
    new_bot['script'] = get_script_response(new_bot['_id'], request.host_url)
    if db.chatbots.insert_one(new_bot):
        return jsonify(success=True)
    return jsonify({ "error": "Bot Creation Failed" })

@app.route('/chat/start', methods=['GET'])
def start_chatbot():
    bot_id = request.args.get('id')
    bot = db.chatbots.find_one({'_id': bot_id})
    namespace = bot['namespace']
    new_qa_chain = QAchain(namespace)
    qa_chain_id = uuid.uuid4().hex
    running_chains[qa_chain_id] = new_qa_chain
    return {
        'qa_chain_id': qa_chain_id
    }

@app.route('/chat/close', methods=['GET'])
def close_chatbot():
    qa_chain_id = request.args.get('id')
    running_chains.pop(qa_chain_id)
    return "QA Chain Closed"

@app.route('/chat/ask', methods=['POST'])
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