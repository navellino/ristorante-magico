from fastapi import FastAPI, Request
import json
import os                
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from operator import itemgetter 

from langchain_community.vectorstores import FAISS
# --- ECCO L'ATTREZZO CORRETTO ---
from langchain_huggingface import HuggingFaceEndpointEmbeddings

load_dotenv()

# --- FUNZIONI DI SUPPORTO ---
def carica_la_dispensa():
    with open("dati.json", "r") as file:
        dati = json.load(file)
    return dati

def get_contesto_utente(booking_id: str) -> dict:
    print(f"Sto cercando il contesto per: {booking_id}")
    dispensa = carica_la_dispensa()
    info_utente = dispensa.get(booking_id, {}) 
    return {
        "nome": info_utente.get("nome_ospite", "Ospite"), 
        "stagione": info_utente.get("stagione", "sconosciuta")
    }

# --- CARICHIAMO TUTTO ALL'AVVIO! ---
print("Accensione cucina: Carico lo 'Chef Magico' (Gemini)...")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

print("Accensione cucina: Carico il 'Traduttore' (API)...")

# --- ECCO LA CORREZIONE CHIAVE ---
NUOVO_URL = "https://router.huggingface.co/hf-inference/sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEndpointEmbeddings(
    endpoint_url=NUOVO_URL, 
    huggingfacehub_api_token=os.getenv("HF_TOKEN")
)

print("Accensione cucina: Carico la 'Dispensa Magica' (faiss_index)...")
db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever(search_kwargs={"k": 1})

templates = Jinja2Templates(directory="templates")
print("--- CUCINA PRONTA E OPERATIVA! ---")

# --- CATENE DI MONTAGGIO (INVARIATE) ---
prompt_benvenuto = ChatPromptTemplate.from_messages(
    [
        ("system", "Sei un assistente concierge amichevole."),
        ("user", "Scrivi un messaggio di benvenuto breve e caloroso per {nome}."
                 "Includi queste info: Wi-Fi: {wifi}, Check-out: {checkout}.")
    ]
)
output_parser = StrOutputParser()
catena_benvenuto = prompt_benvenuto | llm | output_parser

prompt_domanda = ChatPromptTemplate.from_messages(
    [
        ("system", "Sei un assistente concierge. Sei amichevole e professionale."
                   "L'ospite con cui stai parlando si chiama {nome}."
                   "La stagione attuale è {stagione}."
                   "Rispondi alla domanda dell'utente basandoti *solo* sul contesto fornito."),
        ("user", "Contesto Trovato: {contesto}\n\nDomanda dell'Ospite: {domanda}\n\nRisposta:")
    ]
)

catena_domanda = (
    {
        "contesto": itemgetter("domanda") | retriever,
        "info_utente": itemgetter("booking_id") | RunnableLambda(get_contesto_utente),
        "domanda": itemgetter("domanda")
    }
    | RunnablePassthrough.assign(
        nome=RunnableLambda(lambda x: x["info_utente"]["nome"]),
        stagione=RunnableLambda(lambda x: x["info_utente"]["stagione"])
      )
    | prompt_domanda 
    | llm
    | output_parser
)

# --- AVVIO APP E CAMPANELLI (INVARIATI) ---
app = FastAPI()

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

@app.get("/domanda/")
def fai_domanda(domanda: str, booking_id: str):
    if not domanda or not booking_id:
        return {"errore": "Dati mancanti: servono 'domanda' e 'booking_id'."}
    try:
        input_catena = {"domanda": domanda, "booking_id": booking_id}
        risposta_fatta = catena_domanda.invoke(input_catena)
        return {"messaggio_assistente": risposta_fatta}
    except Exception as e:
        return {"errore": f"Il Capocuoco (Domanda) non risponde: {e}"}