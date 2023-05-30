"""Flask configuration."""

JWT_TOKEN_LOCATION = ["cookies"]
JWT_ACCESS_TOKEN_EXPIRES = 60*60*24
JWT_CSRF_CHECK_FORM = True 
JWT_CSRF_IN_COOKIES = False 

CHATBOT_STATIC_PATH = 'chatbot/build'
CHATBOT_SCRIPT_FILE = 'chatbot.js'

PLAN_DETAILS = {
    'Plan1':{'bots':1, 'sources':5, 'messages':1000, 'price':0, 'price_id':'price_1N4q9cIqbPL5X1upGVnE3tNG'},
    'Plan2':{'bots':3, 'sources':100, 'messages':10000, 'price':49, 'price_id':'price_1N4q7OIqbPL5X1upIspqntW2'},
    'Plan3':{'bots':5, 'sources':300, 'messages':25000, 'price':99, 'price_id':'price_1N4q7OIqbPL5X1upaKAZOSaJ'},
    'Plan4':{'bots':10, 'sources':500, 'messages':50000, 'price':199, 'price_id':'price_1N4q7OIqbPL5X1upFcwP8ZAL'},
    'Plan5':{'bots':20, 'sources':1000, 'messages':100000, 'price':499, 'price_id':'price_1N4q7OIqbPL5X1upu5WC09EX'},
    'Plan6':{'bots':30, 'sources':5000, 'messages':200000, 'price':999, 'price_id':'price_1N4q7OIqbPL5X1upPYf1hMVX'},
}
PRICE_PLAN_MAP = { detail['price_id']: plan for plan,detail in PLAN_DETAILS.items() }
BLOCKED_PLAN = "Blocked"

QUERY_LENGTH_LIMIT = 500
QUERY_WAIT_LIMIT = 5
QUERY_LENGTH_ERR_RESPONSE = "That was too long. Try again."
QUERY_WAIT_ERR_RESPONSE = "That was too fast. Slow down."
BOT_MSGS_ERR_RESPONSE = "The monthly limit of messages for this bot is exceeded."
BLOCKED_ERR_RESPONSE = "Account inactive. Please renew your subscription."

CHAT_RETAIN_TIME = 60*60*24
SOURCE_RETAIN_TIME = 60*60*6

DEFAULT_BASE_PROMPT = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say you don't know. DO NOT try to make up an answer.
If the question is not related to the context, politely respond that you are tuned to only answer questions that are related to the context."""

MAIL_SERVER = 's24.wpx.net'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'support@elephant.ai'
MAIL_DEFAULT_SENDER = 'support@elephant.ai'

VERIFICATION_TIME_LIMIT = 60*60
VERIFICATION_MAIL_BODY = 'Click here verify your email {LINK}'
PASSWORD_MAIL_BODY = 'Temporary password for your account is "{PASSWORD}". Make sure to reset it.'


### .env configuration
# MONGODB_URL=
# OPENAI_API_KEY=
# PINECONE_API_KEY=
# PINECONE_ENVIRONMENT=
# PINECONE_INDEX_NAME=
# JWT_SECRET_KEY=
# STRIPE_PUBLISHABLE_KEY=
# STRIPE_SECRET_KEY=
# STRIPE_ENDPOINT_SECRET=
# MAIL_PASSWORD=
# MAIL_TOKEN_SECRET=
