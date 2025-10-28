# 1. Importiamo TUTTI gli "utensili"
from fastapi import FastAPI, Request
import json
import os                
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Utensili del Capocuoco (LangChain)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# --- NOVITÀ: Importiamo nuovi "organizzatori" ---
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from operator import itemgetter # Un "utensile" per prendere pezzi dai dizionari

# Utensili per la Dispensa Magica
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings

# 2. Carichiamo la nostra "scheda telefonica" segreta di Google
load_dotenv()

# --- 3. FUNZIONI DI SUPPORTO ---

# Funzione per caricare la dispensa etichettata (come prima)
def carica_la_dispensa():
    with open("dati.json", "r") as file:
        dati = json.load(file)
    return dati

# --- NOVITÀ: Funzione che estrae il contesto dell'utente ---
# Questa funzione verrà usata DENTRO la catena di montaggio!
def get_contesto_utente(booking_id: str) -> dict:
    """Prende il booking_id e restituisce nome e stagione."""
    print(f"Sto cercando il contesto per: {booking_id}")
    dispensa = carica_la_dispensa()
    info_utente = dispensa.get(booking_id, {}) # Cerca l'ID, se non c'è dà un dizionario vuoto

    return {
        "nome": info_utente.get("nome_ospite", "Ospite"), # Default "Ospite"
        "stagione": info_utente.get("stagione", "sconosciuta") # Default "sconosciuta"
    }

# --- 4. CARICHIAMO TUTTO ALL'AVVIO! ---
print("Accensione cucina: Carico lo 'Chef Magico' (Gemini)...")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

print("Accensione cucina: Carico il 'Traduttore Automatico' (Locale)...")
embeddings = HuggingFaceEndpointEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
    api_key=os.getenv("HF_TOKEN")
)

print("Accensione cucina: Carico la 'Dispensa Magica' (faiss_index)...")
db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever(search_kwargs={"k": 1})

templates = Jinja2Templates(directory="templates")
print("--- CUCINA PRONTA E OPERATIVA! ---")

# --- 5. CATENA DI MONTAGGIO (Per il benvenuto) ---
# (Questa non cambia, la teniamo)
prompt_benvenuto = ChatPromptTemplate.from_messages(
    [
        ("system", "Sei un assistente concierge amichevole."),
        ("user", "Scrivi un messaggio di benvenuto breve e caloroso per {nome}."
                 "Includi queste info: Wi-Fi: {wifi}, Check-out: {checkout}.")
    ]
)
output_parser = StrOutputParser()
catena_benvenuto = prompt_benvenuto | llm | output_parser

# --- 6. LA NUOVA "CATENA DI MONTAGGIO" CONTESTUALE (Per le domande) ---

# --- NUOVO STAMPO: Ora conosce nome e stagione! ---
prompt_domanda = ChatPromptTemplate.from_messages(
    [
        ("system", "Sei un assistente concierge. Sei amichevole e professionale."
                   "L'ospite con cui stai parlando si chiama {nome}."
                   "La stagione attuale è {stagione}."
                   "Rispondi alla domanda dell'utente basandoti *solo* sul contesto fornito."),
        ("user", "Contesto Trovato: {contesto}\n\nDomanda dell'Ospite: {domanda}\n\nRisposta:")
    ]
)

# --- NUOVA CATENA: Più complessa, usa tutto! ---
catena_domanda = (
    {
        # 1. Prende la "domanda" e la passa al "cercatore" (retriever) per trovare il contesto
        "contesto": itemgetter("domanda") | retriever,

        # 2. Prende il "booking_id" e lo passa alla nostra funzione "get_contesto_utente"
        "info_utente": itemgetter("booking_id") | RunnableLambda(get_contesto_utente),

        # 3. Passa la "domanda" originale così com'è
        "domanda": itemgetter("domanda")
    }
    | RunnablePassthrough.assign( # Assegna i risultati di "info_utente" ai campi "nome" e "stagione"
        nome=RunnableLambda(lambda x: x["info_utente"]["nome"]),
        stagione=RunnableLambda(lambda x: x["info_utente"]["stagione"])
      )
    | prompt_domanda  # Mette tutto nello stampo
    | llm             # Dà allo Chef
    | output_parser   # Interpreta
)

# 7. Creiamo il "robot-assistente"
app = FastAPI()

# --- 8. I NOSTRI "CAMPANELLI" ---

@app.get("/", response_class=HTMLResponse)
async def leggi_pagina_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/benvenuto/{nome_appartamento}")
def dai_il_benvenuto(nome_appartamento: str):
    info_richieste = carica_la_dispensa().get(nome_appartamento)
    if not info_richieste: return {"errore": "Appartamento non trovato"}
    try:
        messaggio_finito = catena_benvenuto.invoke({
            "nome": info_richieste['nome_ospite'],
            "wifi": info_richieste['password_wifi'],
            "checkout": info_richieste['check_out']
        })
        return {"messaggio_assistente": messaggio_finito}
    except Exception as e:
        return {"errore": f"Il Capocuoco (Benvenuto) non risponde: {e}"}

# --- MODIFICA: Il campanello ora accetta anche il booking_id! ---
@app.get("/domanda/")
def fai_domanda(domanda: str, booking_id: str):
    if not domanda or not booking_id:
        return {"errore": "Dati mancanti: servono 'domanda' e 'booking_id'."}
    try:
        # 9. Avviamo la NUOVA catena di montaggio!
        # Le diamo sia la domanda che il booking_id
        input_catena = {"domanda": domanda, "booking_id": booking_id}
        risposta_fatta = catena_domanda.invoke(input_catena)

        return {"messaggio_assistente": risposta_fatta}
    except Exception as e:
        return {"errore": f"Il Capocuoco (Domanda) non risponde: {e}"}