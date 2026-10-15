# -*- coding: utf-8 -*-
"""Controllo SENZA intelligenza artificiale delle strutture lette dalla routine Claude.
La routine scrive data/strutture_proposte.json: {id_bando: {quesiti, minuti, soglia, penalita, frasi: {campo: "frase esatta del bando"}}}.
Qui si tiene un valore solo se la sua frase compare davvero nell'estratto del bando (data/coda.json)
e contiene quel numero. Ciò che passa va in data/strutture_verificate.json, che radar.py usa."""
import json, os, re
QUI = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(QUI, 'data')
def norm(t): return re.sub(r'\s+', ' ', t or '').strip().lower()
coda = {c['id']: norm(c['estratto']) for c in json.load(open(os.path.join(D, 'coda.json')))}
prop = json.load(open(os.path.join(D, 'strutture_proposte.json'))) if os.path.exists(os.path.join(D, 'strutture_proposte.json')) else {}
ok = json.load(open(os.path.join(D, 'strutture_verificate.json'))) if os.path.exists(os.path.join(D, 'strutture_verificate.json')) else {}
for bid, p in prop.items():
    testo = coda.get(bid)
    if not testo: continue
    buoni = {}
    for campo in ('quesiti', 'minuti', 'soglia', 'penalita'):
        v, f = p.get(campo), norm((p.get('frasi') or {}).get(campo))
        if v is None or not f or f not in testo: continue
        num = str(v).replace('.', '[,.]')
        if campo == 'soglia' or re.search(r'(?<!\d)' + num + r'(?!\d)', f): buoni[campo] = v
    if 'quesiti' in buoni and 'minuti' in buoni:
        ok[bid] = {'quesiti': buoni['quesiti'], 'minuti': buoni['minuti'], 'opzioni': p.get('opzioni', 4),
                   'penalita': buoni.get('penalita', 0), 'fonte': 'bando', **({'soglia': buoni['soglia']} if 'soglia' in buoni else {})}
        print('verificata', bid, ok[bid])
    else:
        print('scartata', bid, 'campi verificati:', list(buoni))
json.dump(ok, open(os.path.join(D, 'strutture_verificate.json'), 'w'), indent=1)
