import openai
from tqdm.auto import tqdm
import time
import pinecone

OPENAI_API_KEY = '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'
PINECONE_API_KEY = ''
PINECONE_ENVIRONMENT = ''

openai.api_key = OPENAI_API_KEY
pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT
)

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

def pinecone_upsert(data):
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
                    pass
        embeds = [record['embedding'] for record in res['data']]
        # cleanup metadata
        meta_batch = [{
            'source': x['source'],
            'text': x['text'],
        } for x in meta_batch]
        to_upsert = list(zip(sources_batch, embeds, meta_batch))
        
        # upsert to Pinecone
        index_name = ''.join([c for c in domain_name if c.isalnum()]) + str(int(time.time()))
        # check if index already exists (it shouldn't if this is first time)
        if index_name not in pinecone.list_indexes():
            # if does not exist, create index
            pinecone.create_index(
                index_name,
                dimension=len(res['data'][0]['embedding']),
                metric='cosine',
                metadata_config={'indexed': ['source']}
            )
        index = pinecone.Index(index_name)
        index.upsert(vectors=to_upsert)
        return index_name

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
    
    new_index_name = pinecone_upsert(pages)
    return new_index_name

    

class QAchain:
    def __init__(self, index_name):
        self.chat_history = []
        self.index = pinecone.Index(index_name)
        print("QA Chain Started")

    def llm_complete(prompt):
        res = openai.Completion.create(
            engine='gpt-3.5-turbo',
            prompt=prompt,
            temperature=0,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )
        return res['choices'][0]['text'].strip()

    def pinecone_query(self,query):
        embeds = openai.Embedding.create(
            input=[query],
            engine=embed_model
        )
        # retrieve from Pinecone
        xq = embeds['data'][0]['embedding']
        # get relevant vectors
        res = self.index.query(xq, top_k=4, include_metadata=True)
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
        return self.llm_complete(prompt)

    def add_context(self,qn):
        contexts = self.pinecone_query(qn)
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
        qn_with_history = self.condense_history(qn)
        qn_with_context = self.add_context(qn_with_context)
        result = self.llm_complete(qn_with_context)
        self.chat_history.append((qn, result))
        return result
    
    def __del__(self):
        print("QA Chain Closed")
