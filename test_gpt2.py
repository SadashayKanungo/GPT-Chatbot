from gpt2 import create_embeddings, QAchain

sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
domain_name = 'victoriousseo.com/services'

namespace = create_embeddings(sitemap_url, domain_name)

qa = QAchain(namespace)

print("Start Chat")
while True:
    print("Q: ", end='')
    q = input()
    a = qa.ask(q)
    print("A: ", a)