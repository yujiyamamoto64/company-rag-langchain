import os
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


def _format_docs(docs):
    """Junta os textos recuperados em um unico bloco de contexto."""
    return "\n\n".join(doc.page_content for doc in docs)


load_dotenv()

connection_string = os.getenv("PG_CONNECTION")
if not connection_string:
    raise RuntimeError("PG_CONNECTION nao configurada no arquivo .env")

app = FastAPI()
llm = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings()

db = PGVector(
    connection_string=connection_string,
    embedding_function=embeddings,
    collection_name="company_docs",
)

retriever = db.as_retriever(search_kwargs={"k": 4})
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Voce e um assistente especializado em politicas internas. "
                "Use apenas os trechos fornecidos em contexto para responder "
                "e informe quando a informacao nao estiver nos documentos.\n\n"
                "{context}"
            ),
        ),
        ("human", "{question}"),
    ]
)

rag_chain = (
    {
        "context": retriever | RunnableLambda(_format_docs),
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)


@app.get("/ask")
def ask(q: str = Query(..., description="Pergunta do usuario")):
    try:
        answer = rag_chain.invoke(q)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"question": q, "answer": answer}
