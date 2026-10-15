# -*- coding: utf-8 -*-
"""Da un bando inPA al profilo Aura. Prima le regole dei concorsi nazionali
(regole_nazionali.json, le stesse del server), poi le regole generali per figura ed ente.
Restituisce (profilo, gruppo_mancante): uno dei due è None."""
import re, json, os
_QUI = os.path.dirname(os.path.abspath(__file__))
NAZ = {k: v for k, v in json.load(open(os.path.join(_QUI, 'regole_nazionali.json'))).items() if not k.startswith('_')}
ATTI = re.compile(json.load(open(os.path.join(_QUI, 'regole_nazionali.json')))['_atti'], re.I)

def nazionale(titolo, ente):
    for k, r in NAZ.items():
        if 'ente' in r and not re.search(r['ente'], ente, re.I): continue
        if 'titolo' in r and not re.search(r['titolo'], titolo, re.I): continue
        if 'e_titolo' in r and not re.search(r['e_titolo'], titolo, re.I): continue
        return k
    return None

def cl(x):
    f=x['figura'].lower().strip(); e=x['ente'].lower(); ti=x['titolo'].lower()
    t=f+' | '+ti[:260]
    univ=bool(re.search(r'universit|politecnico|scuola normale|sissa|iuav|sant.anna',e))
    ricerca=bool(re.search(r'consiglio nazionale delle ric|\bcnr\b|infn|inaf|ingv|enea|\bcrea\b|istituto nazionale|inapp|agenzia spaziale|ogs|stazione zoologica|area science|istituto italiano di tecn|fondazione',e)) and not univ
    cons=bool(re.search(r'conservatorio|accademia di belle|istituto superiore di studi musicali|accademia nazionale|afam',e))
    scuola=bool(re.search(r'istruzione|ufficio scol|istituto compr|liceo|iis|i\.i\.s|istituto di istruzione',e))
    has=lambda p:re.search(p,f)
    hast=lambda p:re.search(p,t)
    if f=='volontari': return 'capitanerie-di-porto-vsp',None
    if f=='dsga': return 'dsga',None
    if f=='ispettori' and 'guardia di finanza' in e: return 'marescialli-guardia-di-finanza',None
    if 'ispettori dell' in f: return 'allievi-marescialli-carabinieri',None
    if f=='avvocato': return 'asmel-2026-funzionario-avvocato',None
    if f=='consigliere': return None,'consigliere Consob (diritto/economia finanziaria)'
    if 'afam' in f: return None,'docente universitario/AFAM'
    asl=bool(re.search(r'\basl\b|azienda sanit|ausl|asst|azienda ospedal|azienda regionale della salute|azienda per il governo della sanit|ente ospedaliero|azienda socio',e))
    if asl and re.search(r'amministrativ',f) and not re.search(r'infermier|dirigent',f):
        return ('collaboratore-amministrativo-prof-asl' if re.search(r'collaboratore|funzionario|professionale',f) else 'assistente-amministrativo-asl'),None
    # --- non-quiz / non coperti
    if has(r'docent|insegnant|accompagnatore al pianoforte|esperto linguistico|\bcel\b'):
        if cons or has(r'afam|prima fascia|accompagnatore|esperto linguistico|\bcel\b') or univ:
            return None,'docente universitario/AFAM'
        if has(r'irc'): return None,'docente di religione (IRC)'
        if scuola or has(r'secondaria|infanzia|primaria|c\.c\.'):
            if re.search(r'infanzia|primaria|eeee|aaaa|adee|adaa',t) and not re.search(r'secondaria',t): return 'docenti-infanzia-e-primaria',None
            return 'docenti-secondaria-parte-generale',None
        return None,'docente (altro)'
    if has(r'ricercator|post-doc|borsista|research|assegn|incarico di collaborazione|incarico post|3 livello|volontari|project manager|full stack|system manager|building manager|primo tecnologo'):
        return None,'ricercatore / borsista / incarichi di ricerca'
    if has(r'tecnologo') :
        return ('enti-di-ricerca-tecnologi-e-collaboratori',None) if (ricerca or not univ) else (None,'tecnologo universitario / progetto di ricerca')
    if has(r'dirigente medico|medico$|^medico|odontoiatra'): return 'dirigente-medico-parte-generale',None
    if has(r'dirigente (sanitario|psicolog)|psicologo|fisico|ortottista|biolog|chimico|veterinar|farmacista dirigente'): return None,'dirigente sanitario / psicologo / altre professioni sanitarie dirigenziali'
    if has(r'dirigente.*(polizia|comandante)|comandante'): return 'comandante-di-polizia-locale',None
    if has(r'dirigente avvocato'): return None,'dirigente avvocato'
    if has(r'dirigente|direttore (di|esercizio)|ispettore casa|responsabile area|responsabile ufficio'):
        if has(r'amministrativ|contabil') and not has(r'medic'): return 'dirigente-amministrativo-enti-locali',None
        if has(r'responsabile'): return None,'responsabile / posizione organizzativa'
        if has(r'tecnic|lavori pubblici|urbanistic|edilizi|ingegner|architett'): return 'dirigente-tecnico-enti-locali',None
        return None,'dirigente tecnico / altri dirigenti'
    if has(r'conducente di taxi|cuoco|autista|manutentore|operaio|cantonier|operatore generico|operatore tecnico specializzato|esecutore|operatore settore|animatore|accompagnatore - tecnico'):
        if has(r'cuoco|taxi|animatore'): return None,'cuoco / conducente / animatore'
        return 'operaio-specializzato-operatore-tecnico',None
    if has(r'addetto alla sorveglianza'): return None,'addetto sorveglianza portuale'
    # --- sanita
    if has(r'operatore socio|oss'): return 'oss-operatore-socio-sanitario',None
    if has(r'infermier'): return 'infermiere',None
    if has(r'ostetric'): return 'ostetrica',None
    if has(r'fisioterap'): return 'fisioterapista',None
    if has(r'radiologia'): return 'tecnico-sanitario-di-radiologia-medica',None
    if has(r'tecnico (sanitario )?di laboratorio biomedico|tecnico sanitario di laboratorio'): return 'tecnico-di-laboratorio-biomedico',None
    if has(r'neurofisiopat'): return 'tecnico-di-neurofisiopatologia',None
    if has(r'fisiopatologia|perfusion'): return 'tecnico-perfusione-cardiovascolare',None
    if has(r'assistente sanitario'): return 'assistente-sanitario',None
    if has(r'logoped'): return 'logopedista',None
    if has(r'dietista'): return 'dietista',None
    if has(r'educatore professionale'): return 'educatore-professionale-sanitario',None
    if has(r'tecnico di laboratorio'): return 'tecnico-di-laboratorio',None
    if has(r'educatore asil|educatore nido|nido d.infanzia|asili nido|operatore esperto/operatrice esperta nei nidi'): return 'educatore-asilo-nido',None
    if has(r'assistente sociale|socio.?assistenzial|servizi socio|area minori|inclusione|ufficio di piano|pedagogico'):
        return ('assistente-sociale-sanita' if re.search(r'asl|azienda sanitaria|ausl|asst|ospedal|a\.s\.',e) else 'assistente-sociale-enti-locali'),None
    # --- forze/ polizia
    if has(r'vice ispettore del corpo di polizia penitenziaria'): return 'polizia-penitenziaria-vice-ispettori',None
    if has(r'ispettori dell.arma'): return None,'ispettori Arma Carabinieri (ruolo specifico)'
    if has(r'agente.*(polizia|poliza)|agenti di polizia|istruttore.*agente|^istruttore di vigilanza|istruttore.*vigilanza'):
        return ('istruttore-di-vigilanza' if has(r'vigilanza') else 'agente-di-polizia-locale'),None
    if has(r'ufficiale.*polizia locale'): return 'ufficiale-di-polizia-locale',None
    if has(r'funzionario di polizia locale'): return 'funzionario-di-vigilanza',None
    if has(r'^ispettori$'): return None,'ispettori (altri)'
    # --- tecnico-amministrativo
    if has(r'informatic|analista|full stack'):
        if has(r'funzionari'): return 'funzionario-informatico',None
        return 'istruttore-informatico',None
    if has(r'bibliotec|biblioteca|archiv|culturali|museal|attivit. culturali|culturale'):
        return 'istruttore-servizi-culturali-e-biblioteche',None
    if has(r'tributar'): return 'istruttore-tributi',None
    if has(r'anagraf|demografic'): return 'istruttore-servizi-demografici-e-anagrafe',None
    if has(r'geometra|perito edile|perito industriale'): return 'istruttore-tecnico-geometra',None
    if has(r'statistic|scientifico|agrari|agronom|forestal|ambientale|ingegner|architett|comunicazione|specialista per la ricerca|orientamento al lavoro|agro-ambiente|produzione artistico|restauro|ordine') and not has(r'amministrativ'):
        if has(r'ambient') and has(r'istruttore'): return 'istruttore-ambiente-e-ecologia',None
        if has(r'ingegner|architett|agrari|agronom|forestal') : return ('funzionario-tecnico' if has(r'funzionar|dirigent') else 'istruttore-tecnico'),None
        if has(r'statistic'): return 'funzionario-statistico',None
        if has(r'comunicazione'): return 'funzionario-comunicazione',None
        if has(r'orientamento'): return 'funzionario-servizi-per-il-lavoro',None
        if has(r'artistico|restauro'): return 'funzionario-beni-culturali',None
        if has(r'ricerca e l.analisi'): return None,'funzionario specialistico (altro)'
        if univ and has(r'scientifico'): return 'personale-tecnico-amministrativo-universita',None
        if has(r'scientifico'): return None,'funzionario scientifico-tecnologico'
    if has(r'tecnic|lavori pubblici|edilizia|servizi tecnici|urbanistic'):
        if has(r'direttivo'): return 'istruttore-direttivo-tecnico',None
        if has(r'operatore|collaboratore (tecnico|esperto)|operaio|esecutore'): 
            if univ or cons: return 'personale-tecnico-amministrativo-universita',None
            return ('operatore-esperto-ex-cat-b' if has(r'operatore esperto|operatore tecnico esperto') else 'operaio-specializzato-operatore-tecnico'),None
        if has(r'funzionar|specialista|esperto|elevata|ingegnere'): return 'funzionario-tecnico',None
        if has(r'operatore|collaboratore (tecnico|esperto)|operaio|esecutore'): 
            if univ or cons: return 'personale-tecnico-amministrativo-universita',None
            return 'operaio-specializzato-operatore-tecnico',None
        if has(r'assistente tecnico'): return 'assistente-amministrativo',None
        return 'istruttore-tecnico',None
    if has(r'contabil|economico|finanzi|ragioneria|ragioner|processi contabili'):
        if has(r'amministrativ') :
            if has(r'direttivo'): return 'istruttore-direttivo-contabile',None
            if has(r'funzionar|specialista|esperto|elevata|eq'): return 'funzionario-amministrativo-contabile',None
            return 'istruttore-amministrativo-contabile',None
        if has(r'direttivo'): return 'istruttore-direttivo-contabile',None
        if has(r'funzionar|specialista|direttore'): return 'funzionario-contabile',None
        return 'istruttore-contabile',None
    if has(r'amministrativ|gestional|affari generali|giuridic|gestionale|segreteri|servizi di supporto|amministrazione|economico'):
        if univ or cons: return 'personale-tecnico-amministrativo-universita',None
        if has(r'direttivo'): return 'istruttore-direttivo-amministrativo',None
        if has(r'funzionar|specialista|esperto|elevata|e\.q|eq\b'): return 'funzionario-amministrativo',None
        if has(r'collaborator') : return 'collaboratore-amministrativo',None
        if has(r'assistente'): return 'assistente-amministrativo',None
        return 'istruttore-amministrativo',None
    if has(r'operatore esperto|operatore tecnico|operatore$|operatore|esperto tecnico|collaboratore (tecnico|professionale tecnico)'):
        if univ or cons: return 'personale-tecnico-amministrativo-universita',None
        return 'operatore-esperto-ex-cat-b',None
    if has(r'^assistente|assistente'):
        return 'assistente-amministrativo',None
    if has(r'collaborator|area dei collaboratori|area collaboratori'):
        if univ or cons or ricerca: return 'personale-tecnico-amministrativo-universita',None
        return 'collaboratore-amministrativo',None
    if has(r'^funzionari|funzionario|elevat'):
        if univ or cons: return 'personale-tecnico-amministrativo-universita',None
        return 'funzionario-amministrativo',None
    if has(r'istruttor|area istruttori|area degli istruttori|specialista'):
        return 'istruttore-amministrativo',None
    return None,'ALTRO'

def classifica(x):
    """x = {figura, ente, titolo} in minuscolo o no"""
    t = ((x.get('titolo') or '') + ' ' + (x.get('figura') or '')).lower()
    e = (x.get('ente') or '').lower()
    n = nazionale(t, e)
    if n: return n, None
    return cl({'figura': (x.get('figura') or ''), 'ente': e, 'titolo': (x.get('titolo') or '')})
