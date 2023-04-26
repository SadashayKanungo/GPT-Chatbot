from dotenv import load_dotenv
load_dotenv()

from gpt3 import create_embeddings, get_answer

sitemap_url = 'https://www.ecochunk.com/sitemap.xml'
domain_name = 'ecochunk.com'
# sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
# domain_name = 'victoriousseo.com/services'

namespace = create_embeddings(sitemap_url, domain_name)
print(namespace)

# namespace = 'victoriousseocomservices1681740334'
# namespace = 'brandinformers-complete-v4'
# namespace = 'victoriousseocomservices1681755721799'


print("Start Chat")
while True:
    print("Q: ", end='')
    q = input()
    a = get_answer(q, [], namespace)
    print("A: ", a['answer'])


# Does Almond Joy have dark chocolate?
# Is it creamy?