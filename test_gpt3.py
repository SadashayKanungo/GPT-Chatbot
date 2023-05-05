from dotenv import load_dotenv
load_dotenv()

from gpt3 import get_urls_from_sitemap, create_embeddings, get_answer, delete_embeddings

DEFAULT_BASE_PROMPT = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say you don't know. DO NOT try to make up an answer.
If the question is not related to the context, politely respond that you are tuned to only answer questions that are related to the context."""

sitemap_url = 'https://www.ecochunk.com/sitemap.xml'
domain_name = 'ecochunk.com'
# sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
# domain_name = 'victoriousseo.com/services'

# url_list = get_urls_from_sitemap(sitemap_url, domain_name)
# namespace = create_embeddings(url_list, domain_name)
# print(namespace)

namespace = 'ecochunkcom1683273268320'

print("Start Chat")
while True:
    print("Q: ", end='')
    q = input()
    if q=="EXIT":
        break
    a = get_answer(q, [], namespace, DEFAULT_BASE_PROMPT)
    print("A: ", a['answer'])
    print("S: ", a['sources'])
    print("")

# delete_embeddings(namespace)