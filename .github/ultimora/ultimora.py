# -*- coding: utf-8 -*-
"""AIgregatore · Ultim'ora (dal 23/11/2026, chiesto da Manlio).

Gira da solo ogni 10 minuti (GitHub Actions, nessuna intelligenza artificiale, nessun token).
Legge i feed delle nostre testate (solo titolo, testata, ora e link), cerca le notizie appena uscite
che almeno 3 testate diverse hanno già ripreso nelle ultime 3 ore e che il sito non ha ancora,
e le scrive in aigregatore/ultimora.json. La pagina le mostra in cima, col titolo originale.
Al giro completo successivo (7:47, 13:47, 19:47) entrano nel sito con il titolo italiano
e la striscia si svuota da sola (i loro link sono già nel sito).

    python ultimora.py <cartella del sito>      (di solito: aigregatore)
    python ultimora.py <cartella> --prova AAAA-MM-GG-HH:MM file.csv...   (prova su feed salvati)
"""
import csv, datetime as dt, html, json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime

QUI = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "AIgregatore/0.1 (lettore di feed RSS; solo titoli e link)"}
ORE, MAX_NOTIZIE = 6, 4
# «ultim'ora» = notizia che corre: almeno 3 testate nelle ultime 2 ore, oppure almeno 5 nelle ultime 6 (Manlio, 23/11:
# conta il ritmo con cui la riprendono, anche se la notizia è già nel sito)
(ORE_RAPIDA, MIN_RAPIDA), MIN_LARGA = (2, 3), 5
AI = re.compile(r"\b(ai|ia|a\.i\.|intelligenz[ae] artificial[ei]|artificial intelligence|gpt[-\w.]*|chatgpt|openai|claude|anthropic|gemini|llm|llms|agent[ei]?|agents|agentic|copilot|deepseek|llama|mistral|grok|xai|qwen|kimi|chatbot|chatbots|machine learning|deep learning|neural|nvidia|perplexity|midjourney|sora|notebooklm|hugging ?face|agi|superintelligen\w*|deepmind|altman|amodei|hassabis|data ?cent(?:er|re)s?|chip|chips|robot\w*)\b", re.I)
# parole troppo comuni per dire «stesso fatto» (inglese e italiano)
VUOTE = set("""the a an and or of to in on for with by from at as is are was were be been its it this that these those new
says said say after over into about amid than more most will would could can has have had not no but how why what who when
just now first last year years week day today ai artificial intelligence model models company companies tech technology
il lo la i gli le un una uno di da del della dei delle degli nel nella nei sul sulla per con tra fra che non come anche
più dopo prima sono stato stata nuovo nuova nuovi nuove intelligenza artificiale ecco cosa perché sua suo loro report
report reports could amid billion million deal plans plan launch launches data center centers centre centres
black friday deals sale sales chip chips ceo startup startups users user people tools tool agent agents chatbot chatbots""".split())


def leggi_csv(f):
    return list(csv.DictReader(open(f, encoding="utf-8"))) if os.path.exists(f) else []


def items(x):
    out = []
    for it in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", x, re.S):
        g = lambda p: (re.search(p, it, re.S) or [None, ""])[1]
        t = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", g(r"<title[^>]*>(.*?)</title>"))).strip()
        l = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", g(r"<link>(.*?)</link>") or g(r'<link[^>]*href="([^"]+)"'))).strip()
        d = g(r"<(?:pubDate|published|updated|dc:date)>(.*?)</").strip()
        try: d = (parsedate_to_datetime(d) if "," in d else dt.datetime.fromisoformat(d.replace("Z", "+00:00"))).astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
        except Exception: d = ""
        out.append(dict(titolo=t, link=l, data=d))
    return out


def una_fonte(s):
    if s["tipo"] == "feed": u = s["indirizzo"]
    else:
        hl, gl, ceid = ("en-US", "US", "US:en") if s["edizione"] == "us" else ("it", "IT", "IT:it")
        u = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": f"site:{s['indirizzo']} when:1d", "hl": hl, "gl": gl, "ceid": ceid})
    try: x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read().decode("utf-8", "replace")
    except Exception: return []
    out = []
    for i in items(x):
        if s["tipo"] == "gnews": i["titolo"] = re.sub(r"\s+-\s+[^-]+$", "", i["titolo"])
        t = i["titolo"] if s["edizione"] != "it" else re.sub(r"\b(ai|ia|Ai|Ia)\b", "", i["titolo"])  # in italiano «ai» è una preposizione
        if s["filtro"].strip().lower() in ("sì", "si") and not AI.search(t): continue
        out.append(dict(sito=s["sito"], **i))
    return out


def parole(t):
    t = re.sub(r"[’'`]s\b", "", t)
    return {w for w in re.findall(r"[a-zà-ÿ0-9][a-zà-ÿ0-9.\-]*[a-zà-ÿ0-9]|[a-z0-9]", t.lower()) if w not in VUOTE and len(w) > 2}


def cerca(arts, sito_json, ora):
    dati = json.load(open(sito_json, encoding="utf-8")) if os.path.exists(sito_json) else {"news": []}
    sul_sito = {}  # link -> notizia del sito (per usare il suo titolo italiano)
    for n in dati["news"]:
        for a in n.get("ar", []): sul_sito[a[2]] = n
        sul_sito.setdefault(n.get("u"), n)
    inizio = (ora - dt.timedelta(hours=ORE)).strftime("%Y-%m-%d %H:%M"); fine = (ora + dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    visti, R = set(), []
    for a in sorted(arts, key=lambda a: a["data"]):
        if not a["data"] or not (inizio <= a["data"] <= fine) or a["link"] in visti: continue
        visti.add(a["link"]); a["p"] = parole(a["titolo"]); R.append(a)
    # quanto è rara una parola: conta fra i titoli nuovi della finestra
    df = {}
    for a in R:
        for w in a["p"]: df[w] = df.get(w, 0) + 1
    tetto = max(8, 0.15 * len(R))
    rare = lambda p: {w for w in p if df.get(w, 0) <= tetto}
    gruppi = []  # ogni gruppo: articoli + parole «nucleo»
    for a in R:
        ra = rare(a["p"]); best, bs = None, 0
        for g in gruppi:
            s = len(ra & g["nucleo"])
            if s >= 2 and s > bs: best, bs = g, s
        if best is None: gruppi.append(dict(art=[a], nucleo=set(ra)))
        else:
            best["art"].append(a)
            conta = {}
            for x in best["art"]:
                for w in rare(x["p"]): conta[w] = conta.get(w, 0) + 1
            best["nucleo"] = {w for w, c in conta.items() if c >= 2} or best["nucleo"]
    out, da = [], (ora - dt.timedelta(hours=ORE_RAPIDA)).strftime("%Y-%m-%d %H:%M")
    for g in gruppi:
        siti, siti2 = [], []
        for a in g["art"]:
            if a["sito"] not in siti: siti.append(a["sito"])
            if a["data"] >= da and a["sito"] not in siti2: siti2.append(a["sito"])
        if len(siti2) < MIN_RAPIDA and len(siti) < MIN_LARGA: continue
        conta = {}
        for a in g["art"]:
            n = sul_sito.get(a["link"])
            if n: conta[id(n)] = (conta.get(id(n), (0, n))[0] + 1, n)
        nota = max(conta.values(), key=lambda x: x[0])[1] if conta else None
        out.append(dict(siti=siti, siti2=siti2, art=g["art"], sito=nota))
    out.sort(key=lambda g: (-len(g["siti2"]), -len(g["siti"]), g["art"][0]["data"]))
    return out[:MAX_NOTIZIE]


def scrivi(gruppi, cartella, ora):
    acc = {r["sito"]: r["accesso"] for r in leggi_csv(os.path.join(QUI, "accesso.csv"))}
    notizie = []
    for g in gruppi:
        lib = [a for a in g["art"] if acc.get(a["sito"]) == "libero"]
        it = [a for a in g["art"] if a["sito"] in ITALIANE]
        capo = ([a for a in it if a in lib] or it or lib or g["art"])[0]  # meglio un titolo italiano, meglio se gratis
        n = g["sito"]  # già nel sito: titolo italiano e articolo principale del sito
        notizie.append(dict(t=n["t"] if n else capo["titolo"], u=n["u"] if n else capo["link"], gratis=bool(n["g"]) if n else acc.get(capo["sito"]) == "libero",
                            it=bool(n) or capo["sito"] in ITALIANE, primo=g["art"][0]["data"], n2=len(g["siti2"]), n6=len(g["siti"]),
                            ar=[[a["sito"], a["titolo"], a["link"], acc.get(a["sito"]) == "libero"] for a in g["art"]]))
    f = os.path.join(cartella, "ultimora.json")  # si riscrive a ogni controllo: l'ora dice alla pagina «aggiornato alle»
    json.dump(dict(ora=ora.strftime("%Y-%m-%d %H:%M"), notizie=notizie), open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"ultim'ora: {len(notizie)} notizie"); [print(" -", len(n["ar"]), "articoli:", n["t"]) for n in notizie]


ITALIANE = {r["sito"] for r in leggi_csv(os.path.join(QUI, "fonti.csv")) if r["edizione"] == "it"}

if __name__ == "__main__":
    cartella = sys.argv[1]
    if "--prova" in sys.argv:
        k = sys.argv.index("--prova"); ora = dt.datetime.strptime(sys.argv[k + 1], "%Y-%m-%d-%H:%M")
        arts = [r for f in sys.argv[k + 2:] for r in leggi_csv(f)]
        for g in cerca(arts, os.path.join(cartella, "dati.json"), ora):
            print(len(g["siti2"]), "in 2 ore,", len(g["siti"]), "in 6 ore", "(nel sito: " + g["sito"]["t"][:50] + ")" if g["sito"] else "", "|", " | ".join(f"{a['sito']}: {a['titolo'][:70]} [{a['data'][11:]}]" for a in g["art"]))
        sys.exit()
    ora = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    with ThreadPoolExecutor(8) as ex: arts = [a for r in ex.map(una_fonte, leggi_csv(os.path.join(QUI, "fonti.csv"))) for a in r]
    print(f"{len(arts)} voci lette")
    scrivi(cerca(arts, os.path.join(cartella, "dati.json"), ora), cartella, ora)
