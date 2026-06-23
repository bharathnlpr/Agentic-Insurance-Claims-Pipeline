import os
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ======================================================================
# 1. CUSTOM GOOGLE EMBEDDING FUNCTION FOR CHROMADB
# ======================================================================
class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom wrapper to force ChromaDB to use the official Google GenAI SDK
    for generating vector embeddings natively.
    """
    def __init__(self):
        # Initialize the official client
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        # Using text-embedding-004 (the upgraded production version of embedding-001)
        self.model_name = "models/gemini-embedding-001"

    def name(self) -> str:
        """
        Provides a static identity string for this custom embedding function.
        ChromaDB uses this to prevent internal collection configuration conflicts.
        """
        return "gemini_precision_embedder"

    def __call__(self, input_texts: Documents) -> Embeddings:
        # Call the Google GenAI API to embed the batch of documents
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=input_texts
        )
        
        # Extract the vector arrays out of the response payload
        # The SDK returns a list of ContentEmbedding objects containing the values
        return [embedding.values for embedding in result.embeddings]


# ======================================================================
# PATH CONFIGURATIONS
# ======================================================================
POLICY_DOCS_DIR = os.path.join("..", "Data", "Policy Documents")
VECTOR_DB_DIR = os.path.join("..", "Data", "policy_vector_db")

def init_vector_database():
    """
    Initializes the persistent policy document ChromaDB vector store.

    Scans the source directory for raw, unstructured insurance policy text guidelines 
    and terms. Leverages the official Google GenAI SDK and a native text-embedding-004 
    wrapper class to generate high-precision mathematical vector arrays for the document 
    chunks, building out a searchable semantic index optimized for targeted RAG retrieval.

    """
    print("==================================================")
    print("INITIALIZING CHROMADB WITH NATIVE GEMINI EMBEDDINGS")
    print("==================================================\n")

    if not os.path.exists(POLICY_DOCS_DIR):
        print(f"[Error] Policy documents directory missing at: {POLICY_DOCS_DIR}")
        return

    # Instantiate our custom Google embedding engine
    gemini_embedder = GeminiEmbeddingFunction()

    # Create persistent local directory disk storage
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)

    # Create or fetch the collection, linking our Gemini embedder to it
    collection = chroma_client.get_or_create_collection(
        name="client_policies",
        embedding_function=gemini_embedder  # <-- Chroma now automatically calls Gemini for all adds/queries!
    )

    documents_list = []
    metadatas_list = []
    ids_list = []

    print("Reading text documents from disk...")
    for file_name in os.listdir(POLICY_DOCS_DIR):
        if file_name.endswith(".txt"):
            full_file_path = os.path.join(POLICY_DOCS_DIR, file_name)
            policy_id_name = file_name.replace(".txt", "")

            with open(full_file_path, "r", encoding="utf-8") as file:
                content = file.read()

            documents_list.append(content)
            metadatas_list.append({"policy_name": policy_id_name})
            ids_list.append(f"id_{policy_id_name}")
            print(f" -> Prepared for embedding: {file_name}")

    if documents_list:
        print("\nSending blocks to Gemini API and storing vector results in Chroma...")
        # Chroma handles the embedding conversion behind the scenes now using our class
        collection.add(
            documents=documents_list,
            metadatas=metadatas_list,
            ids=ids_list
        )
        print("\n--------------------------------------------------")
        print("SUCCESS: Vector database populated using Gemini Embeddings!")
        print("--------------------------------------------------")
    else:
        print("[Warning] Process stopped: No source text documents located.")

if __name__ == "__main__":
    init_vector_database()