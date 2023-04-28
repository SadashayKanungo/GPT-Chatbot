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

from gpt3 import get_urls_from_sitemap, create_embeddings, delete_embeddings, get_answer

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app)

client = MongoClient(os.getenv("MONGODB_URL"))
db = client.gpt_chatbot
if 'last_access_1' in db.chats.index_information():
    current_expire_seconds = db.chats.index_information()['last_access_1']['expireAfterSeconds']
    if current_expire_seconds != app.config['CHAT_RETAIN_TIME']:
        db.chats.drop_index('last_access_1')
        db.chats.create_index("last_access", expireAfterSeconds=app.config['CHAT_RETAIN_TIME'])
if 'created_at_1' in db.sources.index_information():
    current_expire_seconds = db.sources.index_information()['created_at_1']['expireAfterSeconds']
    if current_expire_seconds != app.config['SOURCES_RETAIN_TIME']:
        db.sources.drop_index('created_at_1')
        db.sources.create_index("created_at_1", expireAfterSeconds=app.config['SOURCES_RETAIN_TIME'])

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "standard_price_id": os.environ["STRIPE_STANDARD_PRICE_ID"],
    "premium_price_id": os.environ["STRIPE_PREMIUM_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
}
stripe.api_key = stripe_keys["secret_key"]

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
    is_signed_in = 'access_token_cookie' in request.cookies
    print(is_signed_in, request.cookies)
    return render_template('home.html', is_signed_in=is_signed_in)

@app.route('/dashboard/')
@jwt_required()
def dashboard():
    if not current_user['token']:
        return jsonify({ "error": "Not Authorized" }), 401

    bots = db.bots.find({'owner':current_user['_id']})
    return render_template('dashboard.html', user=current_user, bots=bots, csrf_token=get_csrf_token(current_user['token']))

@app.route('/account/')
@jwt_required()
def account():
    if not current_user['token']:
        return jsonify({ "error": "Not Authorized" }), 401

    return render_template('account.html', user=current_user)

@app.route('/chatbot/')
@jwt_required()
def chabot():
    bot_id = request.args.get('id')
    bot = db.bots.find_one({'_id':bot_id})
    if not bot:
        return jsonify({ "error": "Chatbot Not Found" }), 404
    if not current_user['token'] or bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401

    return render_template('chatbot.html', user=current_user, bot=bot, csrf_token=get_csrf_token(current_user['token']))

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

# Source Routes
@app.route('/source/')
@jwt_required()
def source():
    source_id = request.args.get('id')
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401

    return render_template('source.html', user=current_user, source=source, csrf_token=get_csrf_token(current_user['token']))

@app.route('/newsource', methods=['POST'])
@jwt_required()
def get_sources():
    user_bot_count = db.bots.count_documents({"owner":current_user['_id']})
    if user_bot_count >= app.config["PLAN_LIMITS"][current_user['plan']]['bots']:
        return jsonify({ "error": "Plan Limit Reached" }), 400
    
    bot_name = request.form.get('name')
    sitemap_url = request.form.get('url')
    domain_name = request.form.get('domain')
    sources_limit = app.config["PLAN_LIMITS"][current_user['plan']]['sources']

    try:
        parsed_urls = get_urls_from_sitemap(sitemap_url, domain_name)
        if not parsed_urls:
            return jsonify({'error':'No URLs Found'}), 500
        urls = []
        for i in range(len(parsed_urls)):
            urls.append({
                'index':i,
                'url':parsed_urls[i],
                'selected':False
            })

        new_source = {
            '_id':uuid.uuid4().hex,
            'owner': current_user['_id'],
            'bot_name': bot_name,
            'sitemap_url': sitemap_url,
            'domain_name': domain_name,
            'limit':sources_limit,
            'urls': urls,
            'selected_nos': 0,
            'created_at': datetime.now(timezone.utc),
        }
        db.sources.insert_one(new_source)
        return jsonify({'id':new_source['_id']}), 200
    except Exception as e:
        print(e)
        return jsonify({'error':'Could Not Process Sitemap'}), 500

@app.route('/source/select', methods=['GET'])
@jwt_required()
def select_url_in_source():
    source_id = request.args.get('id')
    index = int(request.args.get('index'))
    
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    if source['selected_nos'] >= source['limit']:
        return jsonify({ "error": "Plan Limit Reached" }), 400
    if source['urls'][index]['selected']:
        return jsonify({ "error": "URL Already Selected" }), 400
    
    source['urls'][index]['selected'] = True
    sel_no = source['selected_nos'] + 1
    db.sources.find_one_and_update({'_id':source_id}, {'$set': {'urls': source['urls'], 'selected_nos':sel_no}})
    return jsonify(success=True)

@app.route('/source/deselect', methods=['GET'])
@jwt_required()
def deselect_url_in_source():
    source_id = request.args.get('id')
    index = int(request.args.get('index'))
    
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    if not source['urls'][index]['selected']:
        return jsonify({ "error": "URL Not Selected" }), 400
    
    source['urls'][index]['selected'] = False
    sel_no = source['selected_nos'] - 1
    db.sources.find_one_and_update({'_id':source_id}, {'$set': {'urls': source['urls'], 'selected_nos':sel_no}})
    return jsonify(success=True)

@app.route('/source/add', methods=['POST'])
@jwt_required()
def add_url_in_source():
    source_id = request.args.get('id')
    url = request.form.get('url')
    
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    
    source['urls'].append({
                'index':len(source['urls']),
                'url':url,
                'selected':False
            })
    db.sources.find_one_and_update({'_id':source_id}, {'$set': {'urls': source['urls']}})
    return jsonify(success=True)

@app.route('/source/submit', methods=['GET'])
@jwt_required()
def generate_new_bot():
    user_bot_count = db.bots.count_documents({"owner":current_user['_id']})
    if user_bot_count >= app.config["PLAN_LIMITS"][current_user['plan']]['bots']:
        return jsonify({ "error": "Plan Limit reached" }), 400

    source_id = request.args.get('id')
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    
    url_list = [url['url'] for url in source['urls'] if url['selected']]
    domain_name = source['domain_name']
    try:
        namespace = create_embeddings(url_list, domain_name)
        new_bot = {
            '_id': uuid.uuid4().hex,
            'name': source['bot_name'],
            'sitemap_url': source['sitemap_url'],
            'domain_name': source['domain_name'],
            'namespace': namespace,
            'owner': current_user['_id'],
            'sources': url_list,
            'config':{
                'header_text':f'Conversation with {source["bot_name"]}',
                'initial_messages':["Hi! How may I help you?"],
                'accent_color': "#000000",
                'base_prompt': app.config['DEFAULT_BASE_PROMPT']
            }
        }
        new_bot['script'] = get_script_response(new_bot['_id'], request.host_url)
        db.bots.insert_one(new_bot)
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify({ "error": "Bot Creation Failed" }), 500


# Editbot Routes

@app.route('/editbot/delete', methods=['GET'])
@jwt_required()
def delete_bot():
    bot_id = request.args.get('id')
    bot = db.bots.find_one(bot_id)
    if bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    try:
        namespace = bot['namespace']
        delete_embeddings(namespace)
        db.bots.find_one_and_delete({'_id':bot_id})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify({ "error": "Bot Deletion Failed" }), 500

@app.route('/editbot/config', methods=['POST'])
@jwt_required()
def configure_bot():
    bot_id = request.args.get('id')
    new_config = {
        'header_text': request.form.get('header_text'),
        'accent_color': request.form.get('accent_color'),
        'initial_messages':request.form.get('initial_messages').split('\n'),
        'base_prompt':request.form.get('base_prompt'),
    }
    print(new_config)
    
    bot = db.bots.find_one(bot_id)
    if bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    try:
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'config':new_config}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify({ "error": "An Error Occured" }), 500


@app.route('/editbot/sources/add', methods=['POST'])
@jwt_required()
def add_source_bot():
    bot_id = request.args.get('id')
    url = request.form.get('url') 
    bot = db.bots.find_one(bot_id)
    if bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    if url in bot['sources']:
        return jsonify({ "error": "URL Already Preset" }), 400
    try:
        bot['sources'].append(url)
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':bot['sources']}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify({ "error": "An Error Occured" }), 500

@app.route('/editbot/sources/drop', methods=['GET'])
@jwt_required()
def drop_source_bot():
    bot_id = request.args.get('id')
    index = int(request.args.get('index'))
    bot = db.bots.find_one(bot_id)
    if bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    try:
        bot['sources'].pop(index)
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':bot['sources']}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify({ "error": "An Error Occured" }), 500

@app.route('/editbot/regen', methods=['GET'])
@jwt_required()
def regenerate_bot():
    bot_id = request.args.get('id')
    bot = db.bots.find_one(bot_id)
    if not bot:
        return jsonify({ "error": "Bot Not Found" }), 404
    if not current_user['token'] or bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    try:
        delete_embeddings(bot['namespace'])
        namespace = create_embeddings(bot['sources'], bot['domain_name'])
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'namespace':namespace}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify({ "error": "Bot Creation Failed" }), 500

# Chat Routes

@app.route('/chat/start', methods=['GET'])
def start_chatbot():
    bot_id = request.args.get('id')
    cookie_value = request.cookies.get('gptchatbot_cookie')
    if cookie_value:
        # If yes, update last access and set chat obj to found entry
        chat = db.chats.find_one({'_id':cookie_value})
        db.chats.find_one_and_update({'_id':chat['_id']}, {'$set': {'last_access': datetime.now(timezone.utc)}})
    else:
        # If not, create new entry and set chat obj to new entry
        bot = db.bots.find_one({'_id':bot_id})
        if not bot:
            return jsonify({ "error": "Bot Not Found" }), 404
        chat = {
            '_id': uuid.uuid4().hex,
            'bot_id': bot_id,
            'namespace': bot['namespace'],
            'base_prompt': bot['config']['base_prompt'],
            'messages': [],
            'internal_messages': [{"role": "system", "content": "You are a helpful assistant."}],
            'last_access': datetime.utcnow(),
        }
        db.chats.insert_one(chat)
    
    response = jsonify({
        'qa_chain_id': chat['_id'],
        'messages': chat['messages'],
        'config': bot['config'],
    })
    response.set_cookie('gptchatbot_cookie', chat['_id'], max_age=app.config["CHAT_RETAIN_TIME"], secure=True, httponly=True, samesite='None')
    return response

@app.route('/chat/ask', methods=['POST'])
def ask_chatbot():
    qa_chain_id = request.args.get('id')
    qn = request.json['question']
    chat = db.chats.find_one({'_id':qa_chain_id})
    ans = get_answer(qn, chat['internal_messages'], chat['namespace'], chat['base_prompt'])
    updated_messages = chat['messages'] + [{"role":"user", "content":qn}, {"role":"assisstant", "content":ans['answer']}]
    db.chats.find_one_and_update({'_id':qa_chain_id}, {'$set': {
        'messages': updated_messages,
        'internal_messages': ans['internal_messages'],
        'last_access': datetime.now(timezone.utc)
    }})
    response = jsonify({
        'answer': ans['answer']
    })
    response.set_cookie('gptchatbot_cookie', chat['_id'], max_age=app.config["CHAT_RETAIN_TIME"], secure=True, httponly=True, samesite='None')
    return response

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