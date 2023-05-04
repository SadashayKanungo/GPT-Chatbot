"""Flask configuration."""

JWT_TOKEN_LOCATION = ["cookies"]
JWT_ACCESS_TOKEN_EXPIRES = 60*60*24
JWT_CSRF_CHECK_FORM = True 
JWT_CSRF_IN_COOKIES = False 

CHATBOT_STATIC_PATH = 'chatbot/build'
CHATBOT_SCRIPT_FILE = 'chatbot.js'

PLAN_LIMITS = {
    'Starter':{'bots':5, 'sources':10, 'messages':10000},
    'Standard':{'bots':20, 'sources':50, 'messages':50000},
    'Premium':{'bots':50, 'sources':200, 'messages':200000},
}
QUERY_LENGTH_LIMIT = 500
QUERY_WAIT_LIMIT = 10
QUERY_LENGTH_ERR_RESPONSE = "That was too long. Try again."
QUERY_WAIT_ERR_RESPONSE = "That was too fast. Slow down."
BOT_MSGS_ERR_RESPONSE = "The monthly limit of messages for this bot is exceeded."

CHAT_RETAIN_TIME = 60*10
SOURCE_RETAIN_TIME = 60*60*6

DEFAULT_BASE_PROMPT = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say you don't know. DO NOT try to make up an answer.
If the question is not related to the context, politely respond that you are tuned to only answer questions that are related to the context."""

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'gptchatbottesting@gmail.com'
MAIL_DEFAULT_SENDER = 'gptchatbottesting@gmail.com'

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
# STRIPE_STANDARD_PRICE_ID=
# STRIPE_PREMIUM_PRICE_ID=
# STRIPE_ENDPOINT_SECRET=
# MAIL_PASSWORD=
# MAIL_TOKEN_SECRET=