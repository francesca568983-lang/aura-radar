# Routine settimanale di Claude — leggere i bandi difficili (consumo minimo)

1. Leggi `data/coda.json`. **Se è vuoto `[]`, fermati subito: niente da fare.**
2. Per ogni bando in coda (massimo 20, già ordinati per posti) leggi SOLO il campo `estratto`
   (il pezzo del bando sulla prova). Non aprire altro, non navigare.
3. Scrivi `data/strutture_proposte.json`: `{ "<id>": {"quesiti": n, "minuti": n, "opzioni": n, "soglia": n o null,
   "penalita": n o 0, "frasi": {"quesiti": "...", "minuti": "...", "soglia": "...", "penalita": "..."}} }`
   - ogni frase è copiata ESATTAMENTE dall'estratto (stesse parole), è la prova del valore;
   - `soglia` = numero di risposte giuste necessarie su `quesiti` (es. 21/30 su 40 quesiti a +1 → 28);
     se il punteggio ha pesi diversi o non è chiaro, metti null;
   - se un valore non c'è nell'estratto, non inventarlo: lascialo fuori.
4. `python3 verifica.py` → tiene solo i valori le cui frasi esistono davvero nel bando.
5. Commit di `data/strutture_proposte.json` e `data/strutture_verificate.json`, push su main. Fine.
