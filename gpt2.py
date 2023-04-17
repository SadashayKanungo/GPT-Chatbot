import openai
from tqdm.auto import tqdm
import pinecone
import requests
import xmltodict
from bs4 import BeautifulSoup
import time

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

def extract_text_from(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)

def prepare_data_entry(url):
    return {
        'source': url,
        'text': extract_text_from(url)
    }    

def pinecone_upsert(data, domain_name):
    new_namespace = ''.join([c for c in domain_name if c.isalnum()]) + str(int(time.time()))
    batch_size = 100  # how many embeddings we create and insert at once
    for i in tqdm(range(0, len(data), batch_size)):
        # find end of batch
        i_end = min(len(data), i+batch_size)
        meta_batch = data[i:i_end]
        # get ids
        sources_batch = [x['source'] for x in meta_batch]
        # get texts to encode
        texts = [x['text'] for x in meta_batch]
        # create embeddings (try-except added to avoid RateLimitError)
        try:
            res = openai.Embedding.create(input=texts, engine=embed_model)
        except:
            done = False
            while not done:
                time.sleep(5)
                try:
                    res = openai.Embedding.create(input=texts, engine=embed_model)
                    done = True
                except:
                    print("Embedding Failed")
        embeds = [record['embedding'] for record in res['data']]
        # cleanup metadata
        meta_batch = [{
            'source': x['source'],
            'text': x['text'],
        } for x in meta_batch]
        to_upsert = list(zip(sources_batch, embeds, meta_batch))
        index.upsert(vectors=to_upsert, namespace=new_namespace)
        
    return new_namespace

def create_embeddings(sitemap_url, domain_name):
    # returns Pickle filename
    r = requests.get(sitemap_url)
    xml = r.text
    raw = xmltodict.parse(xml)

    pages = []
    for info in raw['urlset']['url']:
        # info example: {'loc': 'https://www.paepper.com/...', 'lastmod': '2021-12-28'}
        url = info['loc']
        if domain_name in url:
            pages.append(prepare_data_entry(url))
    
    new_namespace = pinecone_upsert(pages, domain_name)
    print(new_namespace, "Upload successful")
    return new_namespace

def llm_complete(prompt):
    res = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        temperature=0,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return res['choices'][0]['text'].strip()

class QAchain:
    def __init__(self, namespace):
        self.chat_history = []
        self.index = index
        self.namespace = namespace
        print("QA Chain Started")

    def pinecone_query(self,query):
        embeds = openai.Embedding.create(
            input=[query],
            engine=embed_model
        )
        # retrieve from Pinecone
        xq = embeds['data'][0]['embedding']
        # get relevant vectors
        res = self.index.query(xq, top_k=4, include_metadata=True, namespace=self.namespace)
        contexts = [
            x['metadata']['text'] for x in res['matches']
        ]
        return contexts

    def condense_history(self,qn):
        history = '\n'.join(self.chat_history)
        prompt = """Given the following conversation and a follow up question, 
            rephrase the follow up question to be a standalone question.
            Chat History: {history}
            Follow Up Input: {qn}
            Standalone question:"""
        return llm_complete(prompt)

    def add_context(self,qn):
        limit = 512
        contexts = self.pinecone_query(qn)
        # print("PINECONE RESULT", contexts)
        # build our prompt with the retrieved contexts included
        prompt_start = (
            "Answer the question based on the context below.\n\n"+
            "Context:\n"
        )
        prompt_end = (
            f"\n\nQuestion: {qn}\nAnswer:"
        )
        # append contexts until hitting limit
        for i in range(1, len(contexts)):
            if len("\n\n---\n\n".join(contexts[:i])) >= limit:
                prompt = (
                    prompt_start +
                    "\n\n---\n\n".join(contexts[:i-1]) +
                    prompt_end
                )
                break
            elif i == len(contexts)-1:
                prompt = (
                    prompt_start +
                    "\n\n---\n\n".join(contexts) +
                    prompt_end
                )
        return prompt
    
    def ask(self, qn):
        print(self.chat_history)
        qn_with_history = self.condense_history(qn) if len(self.chat_history)>0 else qn
        print(qn_with_history)
        qn_with_context = self.add_context(qn_with_history)
        print(qn_with_context)
        result = llm_complete(qn_with_context)
        self.chat_history.append(qn)
        self.chat_history.append(result)
        return result
    
    def __del__(self):
        print("QA Chain Closed")
