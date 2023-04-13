import pickle
import requests
import xmltodict
import time

from bs4 import BeautifulSoup
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import ChatVectorDBChain

OPENAI_API_KEY = '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'

def extract_text_from(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, features="html.parser")
    text = soup.get_text()

    lines = (line.strip() for line in text.splitlines())
    return '\n'.join(line for line in lines if line)

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
            pages.append({'text': extract_text_from(url), 'source': url})
    
    text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
    docs, metadatas = [], []
    for page in pages:
        splits = text_splitter.split_text(page['text'])
        docs.extend(splits)
        metadatas.extend([{"source": page['source']}] * len(splits))
        print(f"Split {page['source']} into {len(splits)} chunks")
    
    store = FAISS.from_texts(docs, OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY), metadatas=metadatas)
    
    filename = f"{''.join(c for c in domain_name if c.isalnum())}_{int(time.time())}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(store, f)
    
    return filename

class QAchain:
    CONDENSE_TEMPLATE = """Given the following conversation and a follow up question, 
    rephrase the follow up question to be a standalone question.
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""

    QA_TEMPLATE = """You are an AI assistant for answering questions about Search Engine Optimization Services
    and technical blog posts. You are given the following extracted parts of 
    a long document and a question.
    Question: {question}
    =========
    {context}
    =========
    Answer :"""
    
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(CONDENSE_TEMPLATE)
    QA_PROMPT = PromptTemplate(template=QA_TEMPLATE, input_variables=["question", "context"])
    
    def __init__(self, filename):
        with open(filename, "rb") as f:
            vectorstore = pickle.load(f)
        llm = OpenAI(temperature=0, model_name='gpt-3.5-turbo', max_tokens = 512, openai_api_key=OPENAI_API_KEY)
        self.qa_chain = ChatVectorDBChain.from_llm(
            llm, 
            vectorstore, 
            qa_prompt = self.QA_PROMPT, 
            condense_question_prompt = self.CONDENSE_QUESTION_PROMPT,
        )
        self.chat_history = []
    
    def ask(self, question):
        result = self.qa_chain({"question": question, "chat_history": self.chat_history})
        self.chat_history.append((question, result["answer"]))
        return result
