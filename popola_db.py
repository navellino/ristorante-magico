import os
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

# --- ECCO L'ATTREZZO CORRETTO ---
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

# --- ECCO LA CORREZIONE CHIAVE ---
# Costruiamo l'URL completo = (Nuovo Indirizzo API) + (Nome Modello)
NUOVO_URL = "https://router.huggingface.co/hf-inference/sentence-transformers/all-MiniLM-L6-v2"

embeddings = HuggingFaceEndpointEmbeddings(
    endpoint_url=NUOVO_URL, 
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
)

print("Sto creando l'indice magico (la dispensa)...")
db = FAISS.from_documents(testi_sminuzzati, embeddings)
db.save_local("faiss_index")

print("--- FATTO! ---")
print("La tua 'Dispensa Magica' (faiss_index) è stata creata con successo!")