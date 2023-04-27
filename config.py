"""Flask configuration."""

JWT_TOKEN_LOCATION = ["cookies"]
JWT_ACCESS_TOKEN_EXPIRES = 60*60*24
JWT_CSRF_CHECK_FORM = True 
JWT_CSRF_IN_COOKIES = False 

CHATBOT_STATIC_PATH = 'chatbot/build'
CHATBOT_SCRIPT_FILE = 'chatbot.js'

PLAN_LIMITS = {
    'Starter':{'bots':5, 'sources':10},
    'Standard':{'bots':20, 'sources':50},
    'Premium':{'bots':50, 'sources':200},
}

CHAT_RETAIN_TIME = 60*10
SOURCE_RETAIN_TIME = 60*60*6


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