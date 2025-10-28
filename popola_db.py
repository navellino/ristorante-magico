import os
from dotenv import load_dotenv

# --- Importiamo gli "utensili" ---
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

# --- NOVITÀ: Importiamo il nostro "Traduttore Automatico" locale ---
from langchain_huggingface import HuggingFaceEndpointEmbeddings

print("Avvio il caricamento della conoscenza...")

# Non ci serve più la chiave API di Google per questo script!
# load_dotenv() 

# 1. CARICA IL LIBRO
loader = TextLoader("conoscenza.txt", encoding="utf-8")
documenti = loader.load()
print(f"Ho caricato {len(documenti)} documento/i.")

# 2. SMINUZZA LE PAGINE
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
testi_sminuzzati = text_splitter.split_documents(documenti)
print(f"Ho sminuzzato il testo in {len(testi_sminuzzati)} pezzi.")

# 3. CREA IL "TRADUTTORE" LOCALE
# Diciamo a LangChain di usare il nostro "Mini-Traduttore" locale
# Scegliamo un modello piccolo e multilingue (ottimo per l'italiano)
print("Sto preparando il 'Traduttore Automatico' locale...")
embeddings = HuggingFaceEndpointEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
    api_key=os.getenv("HF_TOKEN")
)

print("Sto creando l'indice magico (la dispensa)...")

# 4. SALVA NELLO SCAFFALE
# Questo ora usa il traduttore locale, non chiama nessuna API!
db = FAISS.from_documents(testi_sminuzzati, embeddings)
db.save_local("faiss_index")

print("--- FATTO! ---")
print("La tua 'Dispensa Magica' (faiss_index) è stata creata con successo!")
print("Ora puoi avviare la cucina principale con 'uvicorn main:app --reload'")