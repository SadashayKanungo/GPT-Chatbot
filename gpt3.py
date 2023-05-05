import openai
from tqdm.auto import tqdm
import pinecone
import requests
from urllib.parse import urljoin
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import re
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone.init(
    api_key = os.getenv("PINECONE_API_KEY"),
    environment = os.getenv("PINECONE_ENVIRONMENT")
)
# check if index already exists (it shouldn't if this is first time)
index_name = os.getenv("PINECONE_INDEX_NAME")
if index_name not in pinecone.list_indexes():
    # if does not exist, create index
    pinecone.create_index(
        index_name,
        dimension=1563,
        metric='cosine',
        metadata_config={'indexed': ['source']}
    )
index = pinecone.Index(index_name)

embed_model = "text-embedding-ada-002"
max_chunks_per_post = 100

###################################################################################################################

def get_urls_from_sitemap(sitemap_url, domain_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'From': 'googlebot(at)googlebot.com',
        }
    
    def normalize_url(url):
        return url if url.endswith('/') else url + '/'

    def extract_links_from_xml(content):
        soup = BeautifulSoup(content, "lxml-xml")
        urls = [normalize_url(loc.string) for loc in soup.select("urlset url loc")]
        sitemap_links = [normalize_url(sitemap_loc.string) for sitemap_loc in soup.select("sitemapindex sitemap loc")]
        return urls, sitemap_links

    def extract_links_from_html(content):
        soup = BeautifulSoup(content, "html.parser")
        urls = [normalize_url(urljoin(sitemap_url, link.get("href"))) for link in soup.find_all("a")]
        return urls

    def is_xml(content):
        return content.startswith('<?xml') or content.startswith('<urlset') or content.startswith('<sitemapindex')

    def fetch_sitemap_content(url):
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.content.decode("utf-8")
        return None

    def process_sitemap(url, visited=set()):
        if url in visited:
            return set()
        visited.add(url)
        content = fetch_sitemap_content(url)
        if not content:
            return set()

        sitemap_domain = urlparse(url).netloc

        def is_same_domain(url):
            return urlparse(url).netloc == sitemap_domain

        def is_web_page(url):
            extensions_to_exclude = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.pdf', '.mp3', '.mp4', '.avi', '.mkv', '.wav', '.ogg', '.zip', '.tar', '.gz', '.rar', '.7z', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.rtf', '.csv', '.json', '.xml')
            return not any(url.endswith(ext+'/') for ext in extensions_to_exclude)

        if is_xml(content):
            urls, sitemap_links = extract_links_from_xml(content)
            urls = set(filter(lambda u: is_same_domain(u) and is_web_page(u), urls))
            for sitemap_link in sitemap_links:
                urls.update(process_sitemap(sitemap_link, visited))
            return urls
        else:
            return set(filter(lambda u: is_same_domain(u) and is_web_page(u), extract_links_from_html(content)))

    url_list = list(process_sitemap(sitemap_url))
    final_list = [url for url in url_list if domain_name in url]
    return final_list

###################################################################################################################

def extract_data_from(url):
    html = requests.get(url, headers={
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }).text
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

def split_text(text, chunk_size, overlap):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    index = 0
    while index < len(sentences):
        chunk = sentences[index:index + chunk_size]
        chunks.append(' '.join(chunk))
        index += chunk_size - overlap
    return chunks

# updated chunkify function
def chunkify(data):
    chunked_data = []
    for post in data:
        clean_text = post["text"].replace('\n', ' ')
        clean_text = re.sub(r' +', ' ', clean_text)
        clean_text = re.sub(r'^[ \t]*\n', '', clean_text, flags=re.MULTILINE)
        text_chunks = split_text(clean_text, chunk_size=8, overlap=2)

        chunk_counter = 0
        for chunk in text_chunks:
            if chunk_counter >= max_chunks_per_post:
                break
            new_post = post.copy()
            new_post["text"] = chunk
            chunked_data.append(new_post)
            chunk_counter += 1
    for idx, item in enumerate(chunked_data):
        item['id'] = f"{item['url']}#{idx}"
    return chunked_data

def add_urls_to_namespace(url_list, namespace):
    data = []
    for url in url_list:
        data.append(extract_data_from(url))
    chunked_data = chunkify(data)
    
    batch_size = 100
    for i in tqdm(range(0, len(chunked_data), batch_size)):
        # find end of batch
        i_end = min(len(chunked_data), i+batch_size)
        meta_batch = chunked_data[i:i_end]
        ids_batch = [x['id'] for x in meta_batch]
        texts = [x['text'] for x in meta_batch]
        try:
            res = openai.Embedding.create(input=texts, engine=embed_model)
        except Exception as e:
            print("ERROR", e)
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
            'title': x['title'],
            'text': x['text'],
            'url': x['url'],
        } for x in meta_batch]
        to_upsert = list(zip(ids_batch, embeds, meta_batch))
        #upsert to Pinecone
        index.upsert(vectors=to_upsert,namespace=namespace)

def create_embeddings(url_list, domain_name):
    new_namespace = ''.join([c for c in domain_name if c.isalnum()]) + str(round(time.time()*1000))
    add_urls_to_namespace(url_list, new_namespace)
    return new_namespace

def delete_embeddings(namespace):
    index.delete(delete_all=True, namespace=namespace)

def delete_urls_from_namespace(url_list, namespace):
    for url in url_list:
        list_of_ids = [url + "#{}".format(i) for i in range(0, 101)]
        index.delete(ids=list_of_ids, namespace=namespace)
###################################################################################################################

CONDENSE_PROMPT = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

QA_PROMPT = """{base_prompt}
####
Context: {context}
Question: {question}
Helpful answer:"""

ASK_MESSAGE = {"role": "system", "content": "You are a helpful assistant."}

def get_source_documents(query, namespace):
        embed_model = "text-embedding-ada-002"
        res = openai.Embedding.create(input=[query], engine=embed_model)
        xq = res['data'][0]['embedding']
        top_k = 4
        pinecone_results = index.query(xq, top_k=top_k, namespace=namespace, include_metadata=True)
        # print("Pinecone Matches", pinecone_results)
        contexts = [x['metadata']['text'] for x in pinecone_results['matches']]
        sources = [x['metadata']['url'] for x in pinecone_results['matches']]
        sources = list(dict.fromkeys(sources))
        return [contexts, sources]

def get_answer(question, internal_messages, namespace, base_prompt):
    # Check if it's a follow-up question (i.e., not the first user message)
        if len(internal_messages) >= 2:
            chat_history = ""
            for message in internal_messages:
                if message['role']!='system':
                    chat_history += f"{message['role'].capitalize()}: {message['content']}\n"
            # print("Chat history: ",chat_history,"\n")
            condense_res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=350,
                temperature=0.1,
                messages= [ASK_MESSAGE] + [{"role": "user", "content": CONDENSE_PROMPT.format(chat_history=chat_history, question=question)}]
            )
            standalone_question = condense_res["choices"][0]["message"]["content"]
            # print("Standalone_question: ",standalone_question,"\n")
            
        else:
            # If it's not a follow-up question, use the user_query directly
            standalone_question = question

        # Retrieve source documents
        source_documents, source_urls = get_source_documents(standalone_question, namespace)
        # print("Context: "+"\n"+source_documents+"\n")

        internal_messages.append({"role": "user", "content": standalone_question})

        # Generate an answer using the QA_PROMPT and the retrieved context
        answer_res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = [ASK_MESSAGE] + [{"role": "user", "content": QA_PROMPT.format(context='\n'.join(source_documents), question=standalone_question, base_prompt=base_prompt)}]
        )

        answer = answer_res["choices"][0]["message"]["content"]
        internal_messages.append({"role": "assistant", "content": answer})
        return {
            'answer': answer,
            'sources': source_urls,
            'internal_messages':internal_messages
        }
