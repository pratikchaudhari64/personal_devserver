import requests
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def get_workex_text_blob():
    NOTION_URL = 'http://localhost:8000/notionapp/page?url=https://www.notion.so/my-work-ex-265de5b2c12380428f0edae3c881a462'

    response = requests.get(NOTION_URL)

    workex_text_blob = response.text

    return workex_text_blob




class Embeddings:
    def __init__(self, GEMINI_EMBEL_MODEL, API_KEY):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=200,chunk_overlap=50,length_function=len,)
        self.embeddings = GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEL_MODEL,google_api_key=API_KEY)
        self.INDEX_DIRECTORY = "gemini_faiss_index"

        pass

    def generate_and_save_embeddings(self, text_blob):
        docs = [Document(page_content=text_blob)]
        chunks = self.text_splitter.split_documents(docs)

        vector_store = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings,
        )

        vector_store.save_local(self.INDEX_DIRECTORY)
        pass

class RAG:
    def __init__(self, GEMINI_EMBED_MODEL, CHAT_MODEL_NAME, API_KEY):
        self.INDEX_DIRECTORY = "gemini_faiss_index"
        self.embeddings = GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL,google_api_key=API_KEY)

        self.vector_store = FAISS.load_local(
            folder_path=self.INDEX_DIRECTORY,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )

        self.llm = ChatGoogleGenerativeAI(
                model=CHAT_MODEL_NAME,
                api_key=API_KEY, 
                temperature=0.4 
            )

        pass

    async def _ask_gemini(self, user_prompt, retrieved_context=""):
        # llm = ChatGoogleGenerativeAI(
        #             model=CHAT_MODEL_NAME,
        #             api_key=API_KEY, 
        #             temperature=0.4 
        #         )

        system_prompt = """You are an AI agent that has access to my full work experience reports and lot of minute details about 
        each project i have worked on throughout my work life. You should answer what the recruiters are looking for but do not overstep if you don't find any relevant work experience in the context and simply back off witha  polite reply.
        Since a CV/resume is generally not enough, i want you to answer the questions that people would
        ask about my work experience and various things i have worked on at various places. Respond to the queries formally, highlight key impact, skills and achievements
        and give concise answers unless explicilty asked for details. You have to market my work experience but also do not talk anything outside the given provided [CONTEXT]
        so that you are not faking it. Never degrade the culture of any of the work places despite the challenges - show the various obstacles faced as opportunities. 
        Make sure the projects worked on while at one company do not mix the ones worked on while at another company.
        Strongly, if you don't know the answer to some question well, just do not answer and politely decline the request. 
        Do not answer in more than 100 words"""
        messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=retrieved_context),
                    HumanMessage(content=user_prompt)
                ]

        async def get_llm_response(messages):
            response = await self.llm.ainvoke(messages)
            return response

        resp = await get_llm_response(messages=messages)


        # print("\n--- Gemini Response ---")
        # print(resp.content)
        # print(resp.usage_metadata)

        return resp

    async def _retrieve_from_vector_store(self, query):

        # vector_store = FAISS.load_local(
        #     folder_path=self.INDEX_DIRECTORY,
        #     embeddings=self.embeddings,
        #     allow_dangerous_deserialization=True
        # )

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        retrieved_docs = await retriever.ainvoke(query)

        return retrieved_docs
    
    async def generate_with_retrieved_docs(self, query):

        retrieved_docs = await self._retrieve_from_vector_store(query)
        all_retrieved_content = "[CONTEXT]: \n"
        for i, docs in enumerate(retrieved_docs):
            all_retrieved_content += docs.page_content
        
        chat_resp = await self._ask_gemini(user_prompt = query, retrieved_context=all_retrieved_content)

        return chat_resp.content
        







# notion_text = get_workex_text_blob()
# GEMINI_EMBEL_MODEL = "gemini-embedding-001"
# API_KEY = open("/home/opc/personal_devserver/.secrets/geminiapi.txt", 'r').read()
# embeddings = Embeddings(GEMINI_EMBEL_MODEL, API_KEY)
# embeddings.generate_and_save_embeddings(text_blob=get_workex_text_blob())


# user_prompt = """what were the major challenges faced while setting up credit facility and its operations?"""
# retrieved_docs = embeddings.retrieve_from_vector_store(query=user_prompt)
# all_retrieved_content = "[CONTEXT]: \n"
# for i, docs in enumerate(retrieved_docs):
#     all_retrieved_content += docs.page_content

# print(all_retrieved_content)
# MODEL_NAME = "gemini-2.5-flash-lite"
# API_KEY = open("/home/opc/personal_devserver/.secrets/geminiapi.txt", 'r').read()


# resp = asyncio.run(ask_gemini(MODEL_NAME=MODEL_NAME, API_KEY=API_KEY, retrieved_context=all_retrieved_content, user_prompt=user_prompt))
# print(resp.content)

if __name__ == "__main__":

    # GEMINI_EMBEL_MODEL = "gemini-embedding-001"
    # API_KEY = open("/home/opc/personal_devserver/.secrets/geminiapi.txt", 'r').read()
    # embeddings = Embeddings(GEMINI_EMBEL_MODEL, API_KEY)
    # embeddings.generate_and_save_embeddings(text_blob=get_workex_text_blob())

    rag = RAG(GEMINI_EMBED_MODEL="gemini-embedding-001",
              CHAT_MODEL_NAME="gemini-2.5-flash-lite",
              API_KEY=open("/home/opc/personal_devserver/.secrets/geminiapi.txt", 'r').read())
    
    llm_resp =  asyncio.run(rag.generate_with_retrieved_docs(query="what all companies have you worked for and in what capacities?"))
    print(llm_resp)

