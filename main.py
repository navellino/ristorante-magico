import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Carichiamo le variabili d'ambiente (anche se non ci servono ora, è buona norma)
load_dotenv()

DB_FILE = "calendario.db"

# --- Funzioni di Supporto (le nostre funzioni intelligenti) ---

def calcola_contesto_stagionale(data_check_in: str) -> str:
    """Legge una data e restituisce un contesto stagionale."""
    try:
        data = datetime.strptime(data_check_in, "%Y-%m-%d").date()
        mese = data.month
        giorno = data.day
        
        if mese == 12 and (giorno > 15 and giorno < 30):
            return "Periodo Natalizio"
        if mese == 4 and (giorno > 1 and giorno < 10):
             return "Periodo Pasquale"
        if mese in [12, 1, 2]: return "Inverno"
        if mese in [6, 7, 8]: return "Estate"
        if mese in [9, 10, 11]: return "Autunno"
        if mese in [3, 4, 5]: return "Primavera"
            
    except Exception as e:
        print(f"Errore calcolo stagione: {e}")
        return "Stagione Sconosciuta"

def get_contesto_utente(booking_id: str) -> dict:
    """Prende il booking_id e restituisce un contesto completo dal database."""
    print(f"Richiesta contesto per: {booking_id}")
    
    # Controlliamo se il DB esiste. Se no, lo creiamo al volo.
    if not os.path.exists(DB_FILE):
        print("ATTENZIONE: Database non trovato. Eseguo crea_calendario.py...")
        # (Qui potremmo chiamare la funzione di creazione, 
        # ma per Render è meglio assicurarsi che il file sia caricato)
        return {"errore": "Database non ancora pronto."}

    connessione = sqlite3.connect(DB_FILE)
    connessione.row_factory = sqlite3.Row 
    cursore = connessione.cursor()
    
    query = """
    SELECT 
        p.nome_ospite, 
        pr.password_wifi, 
        pr.orario_check_out,
        p.data_check_in
    FROM Prenotazioni p
    JOIN Proprieta pr ON p.id_proprieta = pr.id_proprieta
    WHERE p.id_prenotazione = ?
    """
    
    cursore.execute(query, (booking_id,))
    risultato = cursore.fetchone()
    connessione.close()
    
    if risultato:
        stagione_calcolata = calcola_contesto_stagionale(risultato["data_check_in"])
        return {
            "nome": risultato["nome_ospite"],
            "wifi": risultato["password_wifi"],
            "checkout": risultato["orario_check_out"],
            "stagione": stagione_calcolata,
            "data_check_in": risultato["data_check_in"]
        }
    else:
        return {"errore": f"Prenotazione {booking_id} non trovata."}

# --- Avvio dell'App FastAPI ---
app = FastAPI()

# Aggiungiamo il "Buttafuori" (CORS) per permettere a Botpress di chiamarci
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Per ora accetta tutti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IL NOSTRO UNICO "CAMPANELLO" ---
@app.get("/get-context/{booking_id}")
def ricevi_contesto(booking_id: str):
    """Il nostro unico endpoint. Botpress lo chiamerà."""
    if not booking_id:
        return {"errore": "ID Prenotazione mancante"}
    
    contesto = get_contesto_utente(booking_id)
    return contesto

@app.get("/")
def root():
    return {"messaggio": "Server Contesto Host - Attivo"}