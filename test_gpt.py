from gpt import create_embeddings, QAchain

sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
domain_name = 'https://victoriousseo.com/services'

filename = create_embeddings(sitemap_url, domain_name)
# filename = 'httpsvictoriousseocomservices_1681364191.pkl'
print("Model saved", filename)
qa = QAchain(filename)

print("Start Chat")
while True:
    print("Q: ", end='')
    q = input()
    a = qa.ask(q)['answer']
    print("A: ", a)