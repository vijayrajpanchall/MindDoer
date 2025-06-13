from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv
embeddings = OpenAIEmbeddings()
load_dotenv()

llm = ChatOpenAI()

goals = [
    Document(
        page_content="Become an expert in building AI agents using LangChain and LangGraph.",
        metadata={"category": "career", "importance": "high"}
    ),
    Document(
        page_content="Maintain hair and skin health by following a weekly self-care routine.",
        metadata={"category": "health", "importance": "medium"}
    ),
    Document(
        page_content="Improve relationship communication skills with thoughtful WhatsApp responses.",
        metadata={"category": "relationship", "importance": "high"}
    ),
]

vectorstore = FAISS.from_documents(goals, embeddings)
print(goals[0].page_content)
print(vectorstore)

# res = llm.invoke("what is your last updated knowledge")

# print(res.content)
