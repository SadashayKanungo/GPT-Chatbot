from gpt import create_embeddings, QAchain

sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
domain_name = 'https://victoriousseo.com/services'

index_name = create_embeddings(sitemap_url, domain_name)

qa = QAchain(index_name)

print("Start Chat")
while True:
    print("Q: ", end='')
    q = input()
    a = qa.ask(q)
    print("A: ", a)