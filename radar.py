# -*- coding: utf-8 -*-
"""Radar dei bandi di Aura — gira ogni giorno su GitHub, gratis.

1. legge su inPA tutti i bandi aperti con una prova d'esame;
2. scarta gli atti su procedure vecchie (scorrimenti, graduatorie, calendari…);
3. collega ogni bando a un profilo Aura (classifica.py);
4. per i bandi nuovi scarica il PDF e cerca da solo la struttura della prova
   (quesiti, minuti, soglia): la tiene solo se la frase del bando la dice in chiaro;
5. scrive:
   data/bandi.json       i bandi aperti, collegati a un profilo Aura (li legge il sito)
   data/coda.json        i bandi grossi senza struttura trovata: li legge la routine Claude
   data/nuovi_tipi.json  i bandi con prova che non corrispondono a nessun profilo
Niente intelligenza artificiale qui dentro: solo regole e controlli.
"""
import json, os, re, subprocess, sys, time, urllib.request, datetime
from classifica import classifica, ATTI

QUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(QUI, 'data'); CACHE = os.path.join(QUI, 'cache')
API = 'https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/'
SEGNAPOSTO = {999, 9999, 99999999}
CON_PROVA = {'ESAMI', 'TITOLI_ESAMI', 'CORSO_CONCORSO'}
GROSSO = 20            # posti da cui un bando senza struttura va in coda alla routine
MAX_PDF = 250          # PDF nuovi letti per giro (gentilezza verso inPA)

def chiedi(url, dati=None, binario=False):
    req = urllib.request.Request(url, data=json.dumps(dati).encode() if dati else None,
                                 headers={'Content-Type': 'application/json', 'Origin': 'https://www.inpa.gov.it',
                                          'User-Agent': 'aura-radar (auraquizapp.it)'})
    for prova in range(3):
        try:
            r = urllib.request.urlopen(req, timeout=60).read()
            return r if binario else json.loads(r)
        except Exception as e:
            if prova == 2: raise
            time.sleep(5)

def tutti_aperti():
    out, pag = [], 0
    while True:
        d = chiedi(API + f'search-better?page={pag}&size=100', {'text': '', 'status': ['OPEN']})
        out += d['content']; pag += 1
        if pag >= d['totalPages'] or pag > 60: return out

def ente_di(b):
    return ' '.join((e.get('nome', '') if isinstance(e, dict) else str(e)) for e in (b.get('entiRiferimento') or []))

# ── struttura della prova dal testo del bando ─────────────────────────────
def testo_pdf(media_id):
    f = os.path.join(CACHE, media_id + '.txt')
    if os.path.exists(f): return open(f, encoding='utf-8', errors='ignore').read()
    pdf = chiedi('https://portale.inpa.gov.it/api/media/' + media_id, binario=True)
    p = os.path.join(CACHE, media_id + '.pdf'); open(p, 'wb').write(pdf)
    try:
        subprocess.run(['pdftotext', '-layout', p, f], check=True, timeout=60)
    except Exception:
        open(f, 'w').write('')
    os.remove(p)
    return open(f, encoding='utf-8', errors='ignore').read()

def pulito(t): return re.sub(r'\s+', ' ', t)

def finestra_prova(t):
    """i pezzi di testo che parlano della prova a quiz"""
    t = pulito(t)
    pezzi = []
    for m in re.finditer(r'(prova (pre)?selettiva|preselezione|prova scritta|test a risposta multipla|quesiti a risposta multipla)', t, re.I):
        pezzi.append(t[max(0, m.start() - 400): m.end() + 900])
    return pezzi

def struttura_da_testo(t):
    """solo ciò che il bando dice in modo univoco; ogni valore porta la sua frase"""
    s = {}
    for p in finestra_prova(t):
        q = re.findall(r'\b(\d{2,3})\s+(?:quesiti|domande)\b', p, re.I)
        mi = re.findall(r'\b(\d{2,3})\s+minuti\b', p, re.I)
        if q and 'quesiti' not in s and len(set(q)) == 1 and 10 <= int(q[0]) <= 200:
            m = re.search(r'[^.]{0,160}\b' + q[0] + r'\s+(?:quesiti|domande)\b[^.]{0,160}', p, re.I)
            s['quesiti'] = {'valore': int(q[0]), 'frase': m.group(0).strip()}
        if mi and 'minuti' not in s and len(set(mi)) == 1 and 10 <= int(mi[0]) <= 240:
            m = re.search(r'[^.]{0,160}\b' + mi[0] + r'\s+minuti\b[^.]{0,160}', p, re.I)
            s['minuti'] = {'valore': int(mi[0]), 'frase': m.group(0).strip()}
        so = re.findall(r'\b(\d{1,2})\s*/\s*30\b', p)
        if so and 'soglia30' not in s and len(set(so)) == 1 and 15 <= int(so[0]) <= 27:
            m = re.search(r'[^.]{0,160}\b' + so[0] + r'\s*/\s*30\b[^.]{0,160}', p)
            s['soglia30'] = {'valore': int(so[0]), 'frase': m.group(0).strip()}
        pe = re.findall(r'(?:errat[ae]|sbagliat[ae])[^.]{0,60}?[-–]\s*0[,.](\d{1,3})', p, re.I)
        if pe and 'penalita' not in s and len(set(pe)) == 1:
            m = re.search(r'[^.]{0,160}(?:errat[ae]|sbagliat[ae])[^.]{0,60}?[-–]\s*0[,.]' + pe[0] + r'[^.]{0,80}', p, re.I)
            s['penalita'] = {'valore': float('0.' + pe[0]), 'frase': m.group(0).strip()}
    return s

def in_app(s):
    """dalla struttura letta alla prova che usa l'app; None se non basta"""
    if 'quesiti' not in s or 'minuti' not in s: return None
    n = s['quesiti']['valore']
    prova = {'quesiti': n, 'minuti': s['minuti']['valore'], 'opzioni': 4, 'penalita': s.get('penalita', {}).get('valore', 0), 'fonte': 'bando'}
    if 'soglia30' in s and 'penalita' not in s:
        prova['soglia'] = -(-n * s['soglia30']['valore'] // 30)     # giuste necessarie, per eccesso
    return prova

# ── giro ──────────────────────────────────────────────────────────────────
def main():
    os.makedirs(DATA, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
    vecchi = {}
    try: vecchi = {b['id']: b for b in json.load(open(os.path.join(DATA, 'bandi.json')))}
    except Exception: pass
    strutture_ai = {}
    try: strutture_ai = json.load(open(os.path.join(DATA, 'strutture_verificate.json')))
    except Exception: pass

    aperti = tutti_aperti()
    bandi, coda, nuovi_tipi, letti = [], [], {}, 0
    for b in aperti:
        if b.get('tipoProcedura') not in CON_PROVA: continue
        titolo = b.get('titolo') or ''; figura = b.get('figuraRicercata') or ''
        if ATTI.search(titolo + ' ' + figura): continue
        ente = ente_di(b)
        profilo, gruppo = classifica({'figura': figura, 'ente': ente, 'titolo': titolo})
        posti = b.get('numPosti'); posti = None if posti in SEGNAPOSTO else posti
        riga = {'id': b['id'], 'profilo': profilo, 'titolo': titolo[:300], 'figura': figura, 'ente': ente,
                'posti': posti, 'scade': (b.get('dataScadenza') or '')[:10],
                'link': 'https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id=' + b['id']}
        if not profilo:
            nuovi_tipi.setdefault(gruppo or 'altro', []).append(riga); continue

        # struttura: già nota? dal PDF? dalla routine (verificata)?
        v = vecchi.get(b['id'])
        if v and 'struttura_letta' in v:
            riga['struttura_letta'] = v['struttura_letta']
        elif letti < MAX_PDF:
            try:
                d = chiedi(API + b['id'])
                media = [a['mediaId'] for a in (d.get('allegati') or []) if a.get('tipo') == 'BANDO_CONCORSO']
                testo = testo_pdf(media[0]) if media else ''
                riga['struttura_letta'] = struttura_da_testo(testo)
                riga['_estratto'] = ' […] '.join(finestra_prova(testo))[:6000]
                letti += 1
            except Exception as e:
                print('pdf non letto', b['id'], e, file=sys.stderr)
        prova = in_app(riga.get('struttura_letta') or {})
        if not prova and b['id'] in strutture_ai: prova = strutture_ai[b['id']]
        if prova: riga['prova'] = prova
        elif (posti or 0) >= GROSSO and riga.get('_estratto'):
            coda.append({'id': b['id'], 'profilo': profilo, 'titolo': titolo[:200], 'posti': posti, 'estratto': riga['_estratto']})
        riga.pop('_estratto', None)
        bandi.append(riga)

    bandi.sort(key=lambda r: -(r['posti'] or 0)); coda.sort(key=lambda r: -(r['posti'] or 0))
    json.dump(bandi, open(os.path.join(DATA, 'bandi.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump(coda[:20], open(os.path.join(DATA, 'coda.json'), 'w'), ensure_ascii=False, indent=1)
    nt = sorted(({'gruppo': k, 'bandi': len(v), 'posti': sum(x['posti'] or 0 for x in v), 'esempi': v[:5]} for k, v in nuovi_tipi.items()), key=lambda x: -x['posti'])
    json.dump(nt, open(os.path.join(DATA, 'nuovi_tipi.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump({'giro': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z', 'aperti_inpa': len(aperti),
               'con_profilo': len(bandi), 'con_prova_dal_bando': sum(1 for b in bandi if b.get('prova')),
               'in_coda': len(coda[:20]), 'senza_profilo': sum(x['bandi'] for x in nt), 'pdf_letti': letti},
              open(os.path.join(DATA, 'stato.json'), 'w'), indent=1)
    print(open(os.path.join(DATA, 'stato.json')).read())

if __name__ == '__main__':
    main()
