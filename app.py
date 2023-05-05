from flask import Flask, render_template, request, redirect, jsonify, make_response, send_from_directory, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, current_user, jwt_required, JWTManager, get_csrf_token
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import random
import string
import stripe
import uuid
import os

load_dotenv()

from gpt3 import get_urls_from_sitemap, create_embeddings, add_urls_to_namespace, delete_embeddings, delete_urls_from_namespace, get_answer

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(os.getenv("MAIL_TOKEN_SECRET"))

client = MongoClient(os.getenv("MONGODB_URL"))
db = client.gpt_chatbot
if 'last_access_1' in db.chats.index_information():
    current_expire_seconds = db.chats.index_information()['last_access_1']['expireAfterSeconds']
    if current_expire_seconds != app.config['CHAT_RETAIN_TIME']:
        db.chats.drop_index('last_access_1')
        db.chats.create_index("last_access", expireAfterSeconds=app.config['CHAT_RETAIN_TIME'])
else:
    db.chats.create_index("last_access", expireAfterSeconds=app.config['CHAT_RETAIN_TIME'])
if 'created_at_1' in db.sources.index_information():
    current_expire_seconds = db.sources.index_information()['created_at_1']['expireAfterSeconds']
    if current_expire_seconds != app.config['SOURCE_RETAIN_TIME']:
        db.sources.drop_index('created_at_1')
        db.sources.create_index("created_at", expireAfterSeconds=app.config['SOURCE_RETAIN_TIME'])
else:
    db.sources.create_index("created_at", expireAfterSeconds=app.config['SOURCE_RETAIN_TIME'])

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
        "plan":"Starter",
        "isVerified":False
    }

    # Encrypt the password
    user['password'] = bcrypt.generate_password_hash(user['password'])

    # Check for existing email address
    if db.users.find_one({ "email": user['email'] }):
        return jsonify({ "error": "Email address already in use" }), 400
    
    # Send Verification Email
    try:
        verification_token = serializer.dumps(user['email'])
        user_id = user['_id']
        link = url_for('verify_email', id=user_id, token=verification_token, _external=True)
        msg = Message('Confirm Email', recipients=[user['email']])
        msg.body = app.config["VERIFICATION_MAIL_BODY"].format(LINK=link)
        mail.send(msg)
        print(msg.body)
    except Exception as e:
        print(e)
        return jsonify({ "error": "Could not send Verification Email"}), 500
    
    # Add to Database
    if db.users.insert_one(user):
        return jsonify({ "msg": "Verification Email Sent" }), 200
    return jsonify({ "error": "Signup failed" }), 500

@app.route('/user/verifyemail')
def verify_email():
    user_id = request.args.get("id")
    verification_token = request.args.get("token")
    try:
        email = serializer.loads(verification_token, max_age=app.config["VERIFICATION_TIME_LIMIT"])
    except SignatureExpired:
        return render_template("failure.html", text=["This Link has Expired."], link="/", button_text="Home")
    except BadTimeSignature:
        return render_template("failure.html", text=["This Link is Invalid."], link="/", button_text="Home")

    user = db.users.find_one({'_id':user_id})
    if email != user['email']:
        return render_template("failure.html", text=["This Link is Invalid"], link="/", button_text="Home")
    
    # Update Database Database
    db.users.find_one_and_update({'_id':user_id}, {'$set':{'isVerified':True}})
    return render_template("success.html", text=["Your Email is verified."], link="/#signIn", button_text="Sign In")

@app.route('/user/forgotpassword', methods=['POST'])
def forgot_password():
    user = db.users.find_one({
        "email": request.form.get('email')
    })

    if not user:
        return jsonify({ "error": "User Not Found" }), 401
    if not user['isVerified']:
        try:
            verification_token = serializer.dumps(user['email'])
            link = '{request.host_url}verifyemail?id={user._id}&token={verification_token}'
            msg = Message('Confirm Email', recipients=[user['email']])
            msg.body = app.config["VERIFICATION_MAIL_BODY"].format(LINK=link)
            mail.send(msg)
            return jsonify({ "error": "Email Not Verified. Verification Link Sent." }), 401
        except Exception as e:
            print(e)
            return jsonify({ "error": "Could not send Verification Email"}), 500

    # Send Temp Password Email
    try:
        temp_password = ''.join(random.choices(string.ascii_letters+string.digits,k=10))
        hashed_password = bcrypt.generate_password_hash(temp_password)
        msg = Message('Temporary Password', recipients=[user['email']])
        msg.body = app.config["PASSWORD_MAIL_BODY"].format(PASSWORD=temp_password)
        mail.send(msg)
        print(msg.body)
    except Exception as e:
        print(e)
        return jsonify({ "error": "Could not send Temporary Password"}), 500
    
    # Add to Database
    if db.users.find_one_and_update({'_id':user['_id']}, {'$set':{'password':hashed_password}}):
        return jsonify({ "msg": "Temporary Password Sent" }), 200
    return jsonify({ "error": "Password Reset failed" }), 500

@app.route('/user/signout')
@jwt_required()
def signout():
    user = db.users.find_one_and_update({'_id':current_user['_id']}, {'$set': {'token': None}})
    response = make_response(redirect('/'))
    response.delete_cookie('access_token_cookie')
    return response

@app.route('/user/resetpassword', methods=['POST'])
@jwt_required()
def reset_password():
    new_password = request.form.get('password')
    hashed_password = bcrypt.generate_password_hash(new_password)
    # Add to Database
    if db.users.find_one_and_update({'_id':current_user['_id']}, {'$set':{'password':hashed_password}}):
        return jsonify({ "msg": "Password Reset Successful" }), 200
    return jsonify({ "error": "Password Reset Failed" }), 500

@app.route('/user/login', methods=['POST'])
def login():
    user = db.users.find_one({
        "email": request.form.get('email')
    })

    if not user:
        return jsonify({ "error": "User Not Found" }), 401
    if not user['isVerified']:
        try:
            verification_token = serializer.dumps(user['email'])
            user_id = user['_id']
            link = url_for('verify_email', id=user_id, token=verification_token, _external=True)
            msg = Message('Confirm Email', recipients=[user['email']])
            msg.body = app.config["VERIFICATION_MAIL_BODY"].format(LINK=link)
            mail.send(msg)
            return jsonify({ "error": "Email Not Verified. Verification Link Sent." }), 401
        except Exception as e:
            print(e)
            return jsonify({ "error": "Could not send Verification Email"}), 500

    if bcrypt.check_password_hash(user['password'], request.form.get('password')):
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

    return render_template('account.html', user=current_user, csrf_token=get_csrf_token(current_user['token']))

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
def get_iframe_response(bot_id, base_url):
    iframe_response = '<iframe id="gpt-chatbot-iframe" src="CHATBOT_IFRAME_URL" width="100%" height="100%" frameborder="0""></iframe>'
    iframe_response = iframe_response.replace("CHATBOT_IFRAME_URL", f'{base_url}bot?id={bot_id}')
    return iframe_response
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

@app.route('/sourceselected/')
@jwt_required()
def sourceselected():
    source_id = request.args.get('id')
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401

    return render_template('sourceselected.html', user=current_user, source=source, csrf_token=get_csrf_token(current_user['token']))

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
        urls = dict()
        for i in range(len(parsed_urls)):
            urls[str(i)] = {
                'index':i,
                'url':parsed_urls[i],
            }
        new_source = {
            '_id':uuid.uuid4().hex,
            'owner': current_user['_id'],
            'bot_name': bot_name,
            'sitemap_url': sitemap_url,
            'domain_name': domain_name,
            'limit':sources_limit,
            'urls': urls,
            'selected': [],
            'ifBotId': None,
            'created_at': datetime.utcnow(),
        }
        db.sources.insert_one(new_source)
        return jsonify({'id':new_source['_id']}), 200
    except Exception as e:
        print(e)
        return jsonify({'error':'Could Not Process Sitemap'}), 500

@app.route('/source/select', methods=['POST'])
@jwt_required()
def select_url_in_source():
    source_id = request.args.get('id')
    indexes = request.json['indexes']
    
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    if len(indexes)==0 or len(indexes)>source['limit']:
        return jsonify({ "error": "Selection number not valid" }), 401
    
    selected_urls = [ source['urls'][index] for index in indexes ]
    db.sources.find_one_and_update({'_id':source_id}, {'$set': {'selected':selected_urls}})
    return jsonify(success=True)

@app.route('/source/delete', methods=['POST'])
@jwt_required()
def deselect_url_in_source():
    source_id = request.args.get('id')
    indexes = request.json['indexes']
    
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    
    for index in indexes:
        source['urls'].pop(index)
    db.sources.find_one_and_update({'_id':source_id}, {'$set': {'urls': source['urls']}})
    return jsonify(success=True)

# URL parsing functions
def is_same_domain(url, sitemap_url):
    sitemap_domain = urlparse(sitemap_url).netloc
    return urlparse(url).netloc == sitemap_domain
def is_web_page(url):
    extensions_to_exclude = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.pdf', '.mp3', '.mp4', '.avi', '.mkv', '.wav', '.ogg', '.zip', '.tar', '.gz', '.rar', '.7z', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.rtf', '.csv', '.json', '.xml')
    return not any(url.endswith(ext+'/') for ext in extensions_to_exclude)
def normalize_url(url):
        return url if url.endswith('/') else url + '/'
####
@app.route('/source/add', methods=['POST'])
@jwt_required()
def add_url_in_source():
    source_id = request.args.get('id')
    raw_urls = request.form.get('urls').replace('\r','').split('\n')

    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    
    new_urls = [ normalize_url(url) for url in raw_urls if is_web_page(url) and is_same_domain(url, source['sitemap_url']) ]
    url_list = [ url['url'] for url in  list(source['urls'].values()) ]
    new_urls = list(set(new_urls))
    new_urls = [ url for url in new_urls if url not in url_list ]
    last_index = max(list(map(int, source['urls'].keys())))
    for url in new_urls:
        last_index += 1
        source['urls'][str(last_index)] = {
            'index':last_index,
            'url':url,
        }
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
    
    url_list = [url['url'] for url in source['selected']]
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
                'base_prompt': app.config['DEFAULT_BASE_PROMPT'],
                'show_sources': False,
            },
            'query_count':0
        }
        new_bot['script'] = get_script_response(new_bot['_id'], request.host_url)
        new_bot['iframe'] = get_iframe_response(new_bot['_id'], request.host_url)
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
        'initial_messages':request.form.get('initial_messages').replace('\r','').split('\n'),
        'base_prompt':request.form.get('base_prompt'),
        'show_sources': request.form.get('show_sources')=="true",
    }
    
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
    raw_urls = request.form.get('urls').replace('\r','').split('\n')
    bot = db.bots.find_one(bot_id)
    old_sources = bot['sources'].copy()
    if bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    sources_limit = app.config["PLAN_LIMITS"][current_user['plan']]['sources']
    add_limit = sources_limit - len(bot['sources'])
    try:
        new_urls = [ normalize_url(url) for url in raw_urls if is_web_page(url) and is_same_domain(url, bot['sitemap_url']) ]
        new_urls = list(set(new_urls))
        unique_new_urls = [ url for url in new_urls if url not in old_sources ]
        if len(unique_new_urls)==0:
            return jsonify({ "error": "No New Unique URLs to Add"}), 401
        if len(unique_new_urls)>add_limit:
            return jsonify({ "error": "Plan Limit Exceeded" }), 401
        add_urls_to_namespace(unique_new_urls, bot['namespace'])
        final_sources = old_sources + unique_new_urls
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':final_sources}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':old_sources}})
        return jsonify({ "error": "An Error Occured" }), 500

@app.route('/editbot/sources/addsitemap', methods=['POST'])
@jwt_required()
def add_sitemap_bot():
    bot_id = request.args.get('id')
    sitemap_url = request.form.get('url')
    bot = db.bots.find_one(bot_id)
    if not bot:
        return jsonify({ "error": "Bot Not Found" }), 404
    sources_limit = app.config["PLAN_LIMITS"][current_user['plan']]['sources']
    add_limit = sources_limit - len(bot['sources'])
    try:
        parsed_urls = get_urls_from_sitemap(sitemap_url, bot['domain_name'])
        if not parsed_urls:
            return jsonify({'error':'No URLs Found'}), 500
        unique_urls = [ url for url in parsed_urls if url not in bot['sources'] ]
        urls = dict()
        for i in range(len(unique_urls)):
            urls[str(i)] = {
                'index':i,
                'url':unique_urls[i],
            }
        new_source = {
            '_id':uuid.uuid4().hex,
            'owner': current_user['_id'],
            'bot_name': bot['name'],
            'sitemap_url': bot['sitemap_url'],
            'domain_name': bot['domain_name'],
            'limit':add_limit,
            'urls': urls,
            'selected': [],
            'ifBotId': bot['_id'],
            'created_at': datetime.utcnow(),
        }
        db.sources.insert_one(new_source)
        return jsonify({'id':new_source['_id']}), 200
    except Exception as e:
        print(e)
        return jsonify({'error':'Could Not Process Sitemap'}), 500

@app.route('/editbot/sources/addsitemap/submit', methods=['GET'])
@jwt_required()
def add_submit_sitemap_bot():
    bot_id = request.args.get('id')
    source_id = request.args.get('srcid')
    bot = db.bots.find_one(bot_id)
    source = db.sources.find_one({'_id':source_id})
    if not source:
        return jsonify({ "error": "Source Not Found" }), 404
    if not bot:
        return jsonify({ "error": "Bot Not Found" }), 404
    if not current_user['token'] or source['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    
    old_sources = bot['sources'].copy()
    url_list = [url['url'] for url in source['selected']]
    try:
        unique_new_urls = list(set(url_list))
        add_urls_to_namespace(unique_new_urls, bot['namespace'])
        final_sources = old_sources + unique_new_urls
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':final_sources}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':old_sources}})
        return jsonify({ "error": "Bot Creation Failed" }), 500


@app.route('/editbot/sources/drop', methods=['POST'])
@jwt_required()
def drop_source_bot():
    bot_id = request.args.get('id')
    indexes = list(map(int,request.json['indexes']))

    bot = db.bots.find_one(bot_id)
    old_sources = bot['sources'].copy()
    if bot['owner'] != current_user['_id']:
        return jsonify({ "error": "Not Authorized" }), 401
    try:
        urls_to_delete = [ bot['sources'][index] for index in indexes ]
        delete_urls_from_namespace(urls_to_delete, bot['namespace'])
        bot['sources'] = [ bot['sources'][i] for i in range(len(bot['sources'])) if i not in indexes ]
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':bot['sources']}})
        return jsonify(success=True)
    except Exception as e:
        print(e)
        db.bots.find_one_and_update({'_id':bot_id}, {'$set':{'sources':old_sources}})
        return jsonify({ "error": "An Error Occured" }), 500

# Chat Routes

@app.route('/chat/start', methods=['GET'])
def start_chatbot():
    bot_id = request.args.get('id')
    bot = db.bots.find_one({'_id':bot_id})
    if not bot:
        return jsonify({ "error": "Bot Not Found" }), 404
    cookie_value = request.cookies.get('gptchatbot_cookie')
    prev_chat = db.chats.find_one({'_id':cookie_value}) if cookie_value else None
    
    if prev_chat and prev_chat['bot_id']==bot_id:
        chat = prev_chat
        db.chats.find_one_and_update({'_id':chat['_id']}, {'$set': {'last_access': datetime.utcnow()}})
    else:
        chat = {
            '_id': uuid.uuid4().hex,
            'bot_id': bot_id,
            'messages': [],
            'internal_messages': [{"role": "system", "content": "You are a helpful assistant."}],
            'last_access': datetime.utcnow(),
        }
        db.chats.insert_one(chat)
    
    bot['config'].pop('base_prompt')
    response = jsonify({
        'qa_chain_id': chat['_id'],
        'messages': chat['messages'],
        'config': bot['config'],
    })
    response.set_cookie('gptchatbot_cookie', chat['_id'], max_age=app.config["CHAT_RETAIN_TIME"], secure=True, httponly=True, samesite='None')
    return response

# Query Wait check
def wait_is_ok(timestamp):
    current_time = datetime.utcnow()
    duration = timedelta(seconds=app.config["QUERY_WAIT_LIMIT"])
    return (current_time - timestamp) > duration

@app.route('/chat/ask', methods=['POST'])
def ask_chatbot():
    qa_chain_id = request.args.get('id')
    qn = request.json['question']
    chat = db.chats.find_one({'_id':qa_chain_id})
    bot = db.bots.find_one({'_id':chat['bot_id']})
    owner = db.users.find_one({'_id':bot['owner']})
    if bot["query_count"] > app.config['PLAN_LIMITS'][owner['plan']]['messages']:
        return jsonify({ 'answer': app.config["BOT_MSGS_ERR_RESPONSE"], 'sources': [] })
    if len(qn)>app.config["QUERY_LENGTH_LIMIT"]:
        return jsonify({ 'answer': app.config["QUERY_LENGTH_ERR_RESPONSE"], 'sources': [] })
    if not wait_is_ok(chat['last_access']):
        return jsonify({ 'answer': app.config["QUERY_WAIT_ERR_RESPONSE"], 'sources': [] })
    ans = get_answer(qn, chat['internal_messages'], bot['namespace'], bot['config']['base_prompt'])
    updated_messages = chat['messages'] + [{"role":"user", "content":qn}, {"role":"assisstant", "content":ans['answer']}]
    db.bots.find_one_and_update({'_id':bot['_id']},{'$inc':{'query_count':1}})
    db.chats.find_one_and_update({'_id':qa_chain_id}, {'$set': {
        'messages': updated_messages,
        'internal_messages': ans['internal_messages'],
        'last_access': datetime.utcnow()
    }})
    response = jsonify({ 'answer': ans['answer'], 'sources': ans['sources'] })
    response.set_cookie('gptchatbot_cookie', chat['_id'], max_age=app.config["CHAT_RETAIN_TIME"], secure=True, httponly=True, samesite='None')
    return response

# Accent Color Endpoint
@app.route('/accentcolor', methods=['GET'])
def accent_color():
    bot_id = request.args.get('id')
    bot = db.bots.find_one(bot_id)
    if not bot:
        return jsonify({ "error": "Bot Not Found" }), 404
    return jsonify(accent_color=bot['config']['accent_color'])

# Stripe Endpoints

@app.route("/stripe/success")
def success():
    return render_template("success.html", text=[
        "You have successfully subscribed to a new plan.",
        "It my take a while for changes to reflect on the website."
    ], link="/dashboard", button_text="Back to Dashboard")


@app.route("/stripe/cancel")
def cancelled():
    return render_template("failure.html", text=[
        "Checkout was cancelled",
    ], link="/dashboard", button_text="Back to Dashboard")

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