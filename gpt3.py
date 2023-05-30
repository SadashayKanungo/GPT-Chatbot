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
import random

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
    sitemap_domain = urlparse(sitemap_url).netloc
    headers = {
            "authority": f"{sitemap_domain}",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "referer": "https://google.com/",
            "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
    IGNORED_EXTENSIONS = set([
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", 
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", 
    ".ppt", ".pptx", ".zip", ".rar", ".7z", 
    ".exe", ".dmg", ".iso", ".tar", ".gz",
    ".csv"
    ])
    
    def is_file_link(url):
        parsed = urlparse(url)
        base, ext = os.path.splitext(parsed.path)
        return ext.lower() in IGNORED_EXTENSIONS

    def normalize_url(url):
        if not is_file_link(url):
            return url
        return None
    
    def extract_links_from_xml(content):
        soup = BeautifulSoup(content, "lxml-xml")
        urls = [normalize_url(loc.string) for loc in soup.select("urlset url loc") if normalize_url(loc.string)]
        sitemap_links = [normalize_url(sitemap_loc.string) for sitemap_loc in soup.select("sitemapindex sitemap loc") if normalize_url(sitemap_loc.string)]
        return urls, sitemap_links

    def extract_links_from_html(content):
        soup = BeautifulSoup(content, "html.parser")
        urls = [normalize_url(urljoin(sitemap_url, link.get("href"))) for link in soup.find_all("a") if normalize_url(urljoin(sitemap_url, link.get("href")))]
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
    sitemap_domain = urlparse(url).netloc
    headers = {
            "authority": f"{sitemap_domain}",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "referer": "https://google.com/",
            "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
    try:
        html = requests.get(url, headers=headers).text
    except requests.exceptions.RequestException as e:
        return {
            'error': f"Failed to fetch the URL: {e}"
        }

    soup = BeautifulSoup(html, features="html.parser")

    # Extract headers till H4
    headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])

    # Generate TOC
    toc_counts = [0, 0, 0, 0]
    toc = "Table of Contents\n"
    for header in headers:
        level = int(header.name[1])
        toc_counts[level - 1] += 1
        for i in range(level, len(toc_counts)):
            toc_counts[i] = 0
        header_text = header.get_text(strip=True).replace('.', ' ')
        toc_number = '-'.join(str(x) for x in toc_counts[:level] if x > 0)
        toc += f"{toc_number} {header_text}\n"
    toc += ". "

    try:
        raw_text = soup.get_text()
        lines = (line.strip() for line in raw_text.splitlines())
        text = '\n'.join(line for line in lines if line)
    except Exception as e:
        text = f"Failed to extract text from the HTML: {e}"

    try:
        title = soup.title.string
    except Exception as e:
        title = "Failed to extract title from the HTML"

    # Prepend TOC to the text
    text_with_toc = f"{toc}\n{text}"

    return {
        'url': url,
        'title': title,
        'text': text_with_toc,
    }

# def split_text(text, chunk_size, overlap):
#     sentences = re.split(r'(?<=[.!?]) +', text)
#     chunks = []
#     index = 0
#     while index < len(sentences):
#         chunk = sentences[index:index + chunk_size]
#         chunks.append(' '.join(chunk))
#         index += chunk_size - overlap
#     return chunks

def split_sentence(sentence):
    split_sentences = []
    while len(sentence) > 250:
        split_point = sentence.rfind(' ', 0, 250)
        if split_point == -1:
            split_point = 250
        split_sentences.append(sentence[:split_point])
        sentence = sentence[split_point:].lstrip()
    split_sentences.append(sentence)
    return split_sentences

def split_text(text, max_chars, overlap):
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences_limited = []
    for sentence in sentences:
        if len(sentence) >= 500:
            sentence_parts = split_sentence(sentence)  
            for part in sentence_parts:
                sentences_limited.append(part)
        else:
            sentences_limited.append(sentence)

    sentences = sentences_limited

    chunks = []
    index = 0

    while index < len(sentences):
        chunk = []
        char_count = 0
        added_sentences = 0

        while index < len(sentences) and char_count + len(sentences[index]) <= max_chars:
            sentence = sentences[index]
            chunk.append(sentence)
            char_count += len(sentence) + 1  # Add 1 to account for the space between sentences
            index += 1
            added_sentences += 1

        chunks.append(' '.join(chunk))

        # Ensure proper overlap by moving the index back by the overlap value
        if added_sentences > overlap:
            index -= overlap
        else:
            # Make sure we always move forward, even when overlap >= added_sentences
            index -= max(0, overlap - added_sentences)

    return chunks

# updated chunkify function
def chunkify(data):
    chunked_data = []
    for post in data:
        clean_text = post["text"].replace('\n', ' ')
        clean_text = re.sub(r' +', ' ', clean_text)
        clean_text = re.sub(r'^[ \t]*\n', '', clean_text, flags=re.MULTILINE)
        text_chunks = split_text(clean_text, max_chars=1020, overlap=1)

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
        time.sleep(random.uniform(0.1, 0.2))
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
        #print("Pinecone Matches", pinecone_results)
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
            #print("Chat history: ",chat_history,"\n")
            condense_res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=2048,
                temperature=0.1,
                messages= [ASK_MESSAGE] + [{"role": "user", "content": CONDENSE_PROMPT.format(chat_history=chat_history, question=question)}]
            )
            standalone_question = condense_res["choices"][0]["message"]["content"]
            #print("Standalone_question: ",standalone_question,"\n")
            
        else:
            # If it's not a follow-up question, use the user_query directly
            standalone_question = question

        # Retrieve source documents
        source_documents, source_urls = get_source_documents(standalone_question, namespace)
        #print("Context: "+"\n"+"\n".join(source_documents)+"\n")

        internal_messages.append({"role": "user", "content": standalone_question})

        # Generate an answer using the QA_PROMPT and the retrieved context
        answer_res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=2048,
            temperature=0.5,
            messages = [ASK_MESSAGE] + [{"role": "user", "content": QA_PROMPT.format(context='\n'.join(source_documents), question=standalone_question, base_prompt=base_prompt)}]
        )

        answer = answer_res["choices"][0]["message"]["content"]
        internal_messages.append({"role": "assistant", "content": answer})
        return {
            'answer': answer,
            'sources': source_urls,
            'internal_messages':internal_messages
        }
