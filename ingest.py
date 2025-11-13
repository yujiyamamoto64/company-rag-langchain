import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

embeddings = OpenAIEmbeddings()
CONNECTION_STRING = os.getenv("PG_CONNECTION")

PDF_FILES = [
    "data/politicas_cancelamento.pdf",
    "data/procedimentos_operacionais.pdf",
]

documents = []
for path in PDF_FILES:
    loader = PyPDFLoader(path)
    documents.extend(loader.load())

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=["\n\n", "\n", ".", " ", ""],
)
chunks = text_splitter.split_documents(documents)

PGVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    connection_string=CONNECTION_STRING,
    collection_name="company_docs"
)

print(f"{len(chunks)} chunks gerados e salvos no Postgres!")
