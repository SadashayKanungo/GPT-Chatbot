import openai
from tqdm.auto import tqdm
import pinecone
import requests
import xmltodict
from bs4 import BeautifulSoup
import time
import re

OPENAI_API_KEY = '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'
embed_model = "text-embedding-ada-002"

PINECONE_API_KEY = 'cf212d98-5dca-4520-b59c-3159584c5ea8'
PINECONE_ENVIRONMENT = 'us-west4-gcp'
index_name = 'openai-youtube-transcriptions'

openai.api_key = OPENAI_API_KEY
pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT
)
# check if index already exists (it shouldn't if this is first time)
if index_name not in pinecone.list_indexes():
    # if does not exist, create index
    pinecone.create_index(
        index_name,
        dimension=1563,
        metric='cosine',
        metadata_config={'indexed': ['source']}
    )
index = pinecone.Index(index_name)



def extract_data_from(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    raw_text = soup.get_text()
    lines = (line.strip() for line in raw_text.splitlines())
    text = '\n'.join(line for line in lines if line)
    title = soup.title.string
    return {
        'url': url,
        'title': title,
        'text': text,
    }

def pinecone_upsert(data, namespace):
    batch_size = 100
    for i in tqdm(range(0, len(data), batch_size)):
        # find end of batch
        i_end = min(len(data), i+batch_size)
        meta_batch = data[i:i_end]
        ids_batch = [x['id'] for x in meta_batch]
        texts = [x['text'] for x in meta_batch]
        try:
            res = openai.Embedding.create(input=texts, engine=embed_model)
        except Exception as e:
            print(e)
            done = False
            while not done:
                sleep(5)
                try:
                    res = openai.Embedding.create(input=texts, engine=embed_model)
                    done = True
                except:
                    pass
        embeds = [record['embedding'] for record in res['data']]
        # cleanup metadata
        meta_batch = [{
            'title': x['title'],
            'text': x['text'],
            'url': x['url'],
        } for x in meta_batch]
        to_upsert = list(zip(ids_batch, embeds, meta_batch))
        #upsert to Pinecone
        index.upsert(vectors=to_upsert,namespace=namespace)

def split_text(text, chunk_size, overlap):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    index = 0
    
    while index < len(sentences):
        chunk = sentences[index:index + chunk_size]
        chunks.append(' '.join(chunk))
        index += chunk_size - overlap

    return chunks

def chunkify(data):
    chunked_data = []
    for post in data:
        clean_text = post["text"].replace('\n', ' ')
        clean_text = re.sub(r' +', ' ', clean_text)
        clean_text = re.sub(r'^[ \t]*\n', '', clean_text, flags=re.MULTILINE)

        text_chunks = split_text(clean_text, chunk_size=8, overlap=2)
        
        for chunk in text_chunks:
            new_post = post.copy()
            new_post["text"] = chunk
            new_post["id"] = f"{len(chunked_data):010d}"
            chunked_data.append(new_post)
    return chunked_data

def create_embeddings(sitemap_url, domain_name):
    # returns Pickle filename
    r = requests.get(sitemap_url)
    xml = r.text
    raw = xmltodict.parse(xml)

    data = []
    for info in raw['urlset']['url']:
        # info example: {'loc': 'https://www.paepper.com/...', 'lastmod': '2021-12-28'}
        url = info['loc']
        if domain_name in url:
            data.append(extract_data_from(url))
    
    chunked_data = chunkify(data)
    print("Chunked data ", len(chunked_data))
    new_namespace = ''.join([c for c in domain_name if c.isalnum()]) + str(round(time.time()*1000))
    pinecone_upsert(chunked_data, new_namespace)
    print(new_namespace, "Upload successful")
    return new_namespace



class QAchain:
    CONDENSE_PROMPT = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    QA_PROMPT = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say you don't know. DO NOT try to make up an answer.
    If the question is not related to the context, politely respond that you are tuned to only answer questions that are related to the context.
    ####
    Context: {context}
    Question: {question}
    Helpful answer in markdown:"""

    def __init__(self, namespace):
        self.index = index
        self.namespace = namespace
        self.message_counter = 0 
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        self.messages_tracker = [{"role": "system", "content": "You are a helpful assistant."}]
        print("QA Chain Started for namespace", self.namespace)


    def get_source_documents(self, query: str):
        embed_model = "text-embedding-ada-002"
        res = openai.Embedding.create(input=[query], engine=embed_model)
        xq = res['data'][0]['embedding']
        top_k = 4
        pinecone_results = self.index.query(xq, top_k=top_k, namespace=self.namespace, include_metadata=True)
        #print(pinecone_results['matches'])
        contexts = [x['metadata']['text'] for x in pinecone_results['matches']]
        return contexts

    def get_answer(self, user_query: str):
        # Check if it's a follow-up question (i.e., not the first user message)
        if self.message_counter >= 2:
            chat_history = ""
            for message in self.messages_tracker:
                if message['role']!='system':
                    chat_history += f"{message['role'].capitalize()}: {message['content']}\n"
            # print("Chat history: ",chat_history,"\n")
            condense_res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=350,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": self.CONDENSE_PROMPT.format(chat_history=chat_history, question=user_query)}
                ]
            )
            standalone_question = condense_res["choices"][0]["message"]["content"]
            # print("Standalone_question: ",standalone_question,"\n")
            
        else:
            # If it's not a follow-up question, use the user_query directly
            standalone_question = user_query

        # Retrieve source documents
        source_documents = self.get_source_documents(standalone_question)
        # print("Context: "+"\n"+source_documents+"\n")

        self.messages_tracker.append({"role": "user", "content": standalone_question})

        # Generate an answer using the QA_PROMPT and the retrieved context
        answer_res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = self.messages + [{"role": "user", "content": self.QA_PROMPT.format(context='\n'.join(source_documents), question=standalone_question)}]
        )

        answer = answer_res["choices"][0]["message"]["content"]
        self.messages_tracker.append({"role": "assistant", "content": answer})
        # print("messages_tracker: ",self.messages_tracker,"\n")
        return answer
    
    def ask(self, question):
        self.message_counter += 1
        response = self.get_answer(question)
        return response
    
    def __del__(self):
        print("QA Chain Closed")
