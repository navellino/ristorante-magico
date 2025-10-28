import os
from dotenv import load_dotenv

# --- Importiamo gli "utensili" ---
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

# --- Importiamo il traduttore API corretto ---
from langchain_community.embeddings import HuggingFaceHubEmbeddings

print("Avvio il caricamento della conoscenza...")

# --- CORREZIONE: Dobbiamo caricare la chiave API! ---
load_dotenv() 

# 1. CARICA IL LIBRO
loader = TextLoader("conoscenza.txt", encoding="utf-8")
documenti = loader.load()
print(f"Ho caricato {len(documenti)} documento/i.")

# 2. SMINUZZA LE PAGINE
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
testi_sminuzzati = text_splitter.split_documents(documenti)
print(f"Ho sminuzzato il testo in {len(testi_sminuzzati)} pezzi.")

# 3. CREA IL "TRADUTTORE" (API)
print("Sto preparando il 'Traduttore' (API)...")
embeddings = HuggingFaceHubEmbeddings(
    repo_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
)

print("Sto creando l'indice magico (la dispensa)...")

# 4. SALVA NELLO SCAFFALE
db = FAISS.from_documents(testi_sminuzzati, embeddings)
db.save_local("faiss_index")

print("--- FATTO! ---")
print("La tua 'Dispensa Magica' (faiss_index) è stata creata con successo!")
print("Questo script ha finito. Ora il server principale si avvierà.")