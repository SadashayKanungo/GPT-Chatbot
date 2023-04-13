from gpt import create_embeddings, QAchain

sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
domain_name = 'https://victoriousseo.com/services'

filename = create_embeddings(sitemap_url, domain_name)
print("Model saved", filename)
qa = QAchain(filename)

print("Start Chat")
while True:
    q = input()
    a = qa.ask(q)
    print(a)