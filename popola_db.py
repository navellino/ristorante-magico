import os
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings

print("Avvio il caricamento della conoscenza...")
load_dotenv() 

loader = TextLoader("conoscenza.txt", encoding="utf-8")
documenti = loader.load()
print(f"Ho caricato {len(documenti)} documento/i.")

text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
testi_sminuzzati = text_splitter.split_documents(documenti)
print(f"Ho sminuzzato il testo in {len(testi_sminuzzati)} pezzi.")

print("Sto preparando il 'Traduttore' (API)...")

# --- ECCO LA CORREZIONE FINALE E SEMPLIFICATA ---
embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2", 
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
)

print("Sto creando l'indice magico (la dispensa)...")
db = FAISS.from_documents(testi_sminuzzati, embeddings)
db.save_local("faiss_index")

print("--- FATTO! ---")
print("La tua 'Dispensa Magica' (faiss_index) è stata creata con successo!")