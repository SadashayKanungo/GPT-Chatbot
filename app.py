from flask import Flask, render_template, request, redirect, jsonify, make_response, send_from_directory
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, current_user, jwt_required, JWTManager, get_csrf_token
from datetime import datetime, timezone
import stripe
import uuid
import os

load_dotenv()

from gpt3 import create_embeddings, get_answer

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app)

client = MongoClient(os.getenv("MONGODB_URL"))
db = client.gpt_chatbot
# db.chats.ensure_index("last_access", expireAfterSeconds=app.config['CHAT_RETAIN_TIME'])
db.chats.create_index("last_access", expireAfterSeconds=app.config['CHAT_RETAIN_TIME'])

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "standard_price_id": os.environ["STRIPE_STANDARD_PRICE_ID"],
    "premium_price_id": os.environ["STRIPE_PREMIUM_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
}
stripe.api_key = stripe_keys["secret_key"]

# running_chains = dict()

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
        "token": None,
        "plan":"Starter"
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

@app.route('/account/')
@jwt_required()
def account():
    if not current_user['token']:
        return jsonify({ "error": "Not Authorized" }), 401

    return render_template('account.html', user=current_user)

@app.route('/bot/', defaults={'path': ''})
@app.route('/bot/<path:path>')
def serve(path):
    if path != "":
        return send_from_directory(app.config['CHATBOT_STATIC_PATH'], path, as_attachment=False)
    else:
        return send_from_directory(app.config['CHATBOT_STATIC_PATH'], 'index.html', as_attachment=False)

# Bot Script Generation
def get_script_response(bot_id, base_url):
    script_response = '<script src="CHATBOT_SCRIPT_URL" id="CHATBOT_ID"></script>'
    script_response = script_response.replace("CHATBOT_ID",bot_id)
    script_response = script_response.replace("CHATBOT_SCRIPT_URL", f'{base_url}static/js/{app.config["CHATBOT_SCRIPT_FILE"]}')
    return script_response

# Bot Functioning Routes
@app.route('/newbot/', methods=['POST'])
@jwt_required()
def generate_new_bot():
    user_bot_count = db.chatbots.count_documents({"owner":current_user['_id']})
    if user_bot_count >= app.config["PLAN_LIMITS"][current_user['plan']]:
        return jsonify({ "error": "Plan Limit reached" }), 501

    bot_name = request.form.get('name')
    sitemap_url = request.form.get('url')
    domain_name = request.form.get('domain')
    
    try:
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
        db.chatbots.insert_one(new_bot)
        return jsonify(success=True)
    except:
        return jsonify({ "error": "Bot Creation Failed" }), 501

@app.route('/chat/start', methods=['GET'])
def start_chatbot():
    bot_id = request.args.get('id')
    ip_addr = str(request.remote_addr)
    # Check if chat entry with same bot id and ip addr
    prev_chat = db.chats.find_one({'bot_id':bot_id, 'ip_addr': ip_addr})
    if prev_chat:
        # If yes, update last access and set chat obj to found entry
        db.chats.find_one_and_update({'_id':prev_chat['_id']}, {'$set': {'last_access': datetime.now(timezone.utc)}})
        chat = prev_chat
    else:
        # If not, create new entry and set chat obj to new entry
        bot = db.chatbots.find_one({'_id':bot_id})
        chat = {
            '_id': uuid.uuid4().hex,
            'bot_id': bot_id,
            'ip_addr': ip_addr,
            'namespace': bot['namespace'],
            'messages': [],
            'internal_messages': [{"role": "system", "content": "You are a helpful assistant."}],
            'last_access': datetime.utcnow(),
        }
        db.chats.insert_one(chat)
    
    # Create qa_chain object from chat
    # bot = db.chatbots.find_one({'_id':bot_id})
    # new_qa_chain = QAchain(bot['namespace'], chat['messages'], chat['internal_messages'])
    # running_chains[chat['_id']] = new_qa_chain
    return {
        'qa_chain_id': chat['_id'],
        'messages': chat['messages']
    }

# @app.route('/chat/close', methods=['GET'])
# def close_chatbot():
#     qa_chain_id = request.args.get('id')
#     qa_chain = running_chains[qa_chain_id]
#     message_dict = qa_chain.get_messages()
#     db.chats.find_one_and_update({'_id':qa_chain_id}, {'$set': {
#         'messages': message_dict['messages'],
#         'internal_messages': message_dict['internal_messages'],
#         'last_access': datetime.now(timezone.utc)
#     }})
#     running_chains.pop(qa_chain_id)
#     return "QA Chain Closed"

@app.route('/chat/ask', methods=['POST'])
def ask_chatbot():
    qa_chain_id = request.args.get('id')
    qn = request.json['question']
    # qa_chain = running_chains[qa_chain_id]
    # ans = qa_chain.ask(qn)
    chat = db.chats.find_one({'_id':qa_chain_id})
    response = get_answer(qn, chat['internal_messages'], chat['namespace'])
    updated_messages = chat['messages'] + [{"role":"user", "content":qn}, {"role":"assisstant", "content":response['answer']}]
    # message_dict = qa_chain.get_messages()
    db.chats.find_one_and_update({'_id':qa_chain_id}, {'$set': {
        'messages': updated_messages,
        'internal_messages': response['internal_messages'],
        'last_access': datetime.now(timezone.utc)
    }})
    return {
        'answer': response['answer']
    }

# Stripe Endpoints

@app.route("/stripe/success")
def success():
    return render_template("success.html")


@app.route("/stripe/cancel")
def cancelled():
    return render_template("cancel.html")

@app.route("/stripe/config")
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)

@app.route("/stripe/create-checkout-session")
@jwt_required()
def create_checkout_session():
    domain_url = request.host_url
    stripe.api_key = stripe_keys["secret_key"]
    plan = request.args.get('plan')
    price_of_plan = {
        'Standard': stripe_keys["standard_price_id"],
        'Premium': stripe_keys["premium_price_id"]
    }
    price_id = price_of_plan[plan]

    try:
        checkout_session = stripe.checkout.Session.create(
            # you should get the user id here and pass it along as 'client_reference_id'
            #
            # this will allow you to associate the Stripe session with
            # the user saved in your database
            #
            client_reference_id=current_user['_id'],
            success_url=domain_url + "stripe/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "stripe/cancel",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1
                }
            ]
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )

    except ValueError as e:
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return "Invalid signature", 400

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        expanded_session = stripe.checkout.Session.retrieve(session.id, expand=["line_items"])
        # Fulfill the purchase...
        handle_checkout_session(expanded_session)

    return "Success", 200

def handle_checkout_session(session):
    buyer_id = session["client_reference_id"]
    plan = session.line_items.data[0]["description"]
    db.users.find_one_and_update({'_id':buyer_id}, {'$set': {'plan': plan}})
    print("Subscription was successful. Database Updated.", buyer_id, plan)


if __name__ == "__main__":
    app.run(debug=True)