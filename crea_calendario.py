import sqlite3
import os

DB_FILE = "calendario.db"

# Rimuoviamo il vecchio database se esiste, per ricominciare
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

# Ci colleghiamo al database (che viene creato se non esiste)
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# --- 1. Creiamo la tabella "Proprieta" ---
# Qui mettiamo le info "fisse" (Wi-Fi, check-out)
cursor.execute("""
CREATE TABLE Proprieta (
    id_proprieta TEXT PRIMARY KEY,
    nome_struttura TEXT,
    password_wifi TEXT,
    orario_check_out TEXT
);
""")

# --- 2. Creiamo la tabella "Prenotazioni" (Il Calendario!) ---
# Qui mettiamo le info "variabili" (l'ospite e le date)
cursor.execute("""
CREATE TABLE Prenotazioni (
    id_prenotazione TEXT PRIMARY KEY,
    id_proprieta TEXT,
    nome_ospite TEXT,
    data_check_in TEXT,
    data_check_out TEXT,
    FOREIGN KEY (id_proprieta) REFERENCES Proprieta (id_proprieta)
);
""")

print("Tabelle 'Proprieta' e 'Prenotazioni' create.")

# --- 3. Riempiamo le tabelle con i nostri dati di test ---

# Aggiungiamo le proprietà
cursor.execute("INSERT INTO Proprieta VALUES ('villa_mare', 'Villa Mare', 'Sole123', '11:00')")
cursor.execute("INSERT INTO Proprieta VALUES ('baita_monti', 'Baita Monti', 'Neve456', '10:00')")

# Aggiungiamo le prenotazioni (IL CALENDARIO!)
# Prenotazione a ridosso di Natale
cursor.execute("INSERT INTO Prenotazioni VALUES ('booking_123', 'villa_mare', 'Mario Rossi', '2025-12-20', '2025-12-27')")
# Prenotazione estiva
cursor.execute("INSERT INTO Prenotazioni VALUES ('booking_456', 'baita_monti', 'Luigi Bianchi', '2025-08-10', '2025-08-17')")
# Prenotazione a Pasqua
cursor.execute("INSERT INTO Prenotazioni VALUES ('booking_789', 'villa_mare', 'Anna Verdi', '2026-04-03', '2026-04-06')")

print("Dati di test inseriti.")

# Salviamo le modifiche e chiudiamo
conn.commit()
conn.close()

print(f"Database '{DB_FILE}' creato e popolato con successo!")
print("Ora puoi eliminare il vecchio 'dati.json' e avviare 'main.py'.")