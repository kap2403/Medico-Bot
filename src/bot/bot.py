import os
import toml
from typing import Optional
from groq import Groq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
import logging
from langchain_groq import ChatGroq
from src.bot.extract_metadata import Metadata


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Medibot:
    def __init__(self, config_path: str = "src/bot/configs/prompt.toml",
                 metadata_database: str = "database/metadata.csv",
                 faiss_database: str = "database/faiss_index" 
                 ):
        """Initialize Medibot with configuration and Groq client."""
        # Load environment variables
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            raise ValueError("GROQ_API_KEY is required")

        # Load prompt configuration
        try:
            config = toml.load(config_path)
            system_prompt = config["rag_prompt"]["system_prompt"]
            user_prompt_template = config["rag_prompt"]["user_prompt_template"]
            
        except (FileNotFoundError, toml.TomlDecodeError) as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise

        # Initialize prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt_template)
        ])

        # initialize vector database
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        vector_store = FAISS.load_local(
                        faiss_database, embeddings, allow_dangerous_deserialization=True
                    )
        self.retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 10})
        # Initialize Groq client
        
        self.model = ChatGroq(
                            model="llama-3.1-8b-instant",
                            temperature=0.2,
                            max_tokens=None,
                            timeout=None,
                            max_retries=2,
                            )
        
        self.metadata_extactor = Metadata(metadata_database)

    
    def query(self, question: str) -> str:
        retrieved_docs = self.retriever.invoke(question)

        # RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
        rag_chain = (
            RunnableParallel({
            "context": RunnableLambda(lambda _: retrieved_docs),  # Reuse retrieved docs
            "question": RunnablePassthrough()
        })
            | self.prompt_template
            | self.model
            | StrOutputParser()
        )

        answer = rag_chain.invoke({"question": question})

        refered_tables , refered_images = self.metadata_extactor.get_data_from_ref(retrieved_docs)
        return answer, retrieved_docs, refered_tables , refered_images