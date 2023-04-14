from gpt import create_embeddings, QAchain

sitemap_url = 'https://victoriousseo.com/page-sitemap.xml'
domain_name = 'https://victoriousseo.com/services'

data = create_embeddings(sitemap_url, domain_name)
# data = 'httpsvictoriousseocomservices_1681364191.pkl'
# print("Model saved, ", len(data))
qa = QAchain(data)

print("Start Chat")
while True:
    print("Q: ", end='')
    q = input()
    a = qa.ask(q)['answer']
    print("A: ", a)