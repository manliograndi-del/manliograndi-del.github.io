# -*- coding: utf-8 -*-
"""AIgregatore · la ricerca generale di Google News sull'AI (chiesto da Manlio il 27/11/2026). Zero token, nessuna IA.

Due ricerche, le stesse che Manlio fa a mano, a ogni aggiornamento (ogni ora su GitHub e nei 3 giri completi):
  USA   «artificial intelligence»   https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en
  Italia «intelligenza artificiale» https://news.google.com/rss/search?q=intelligenza+artificiale&hl=it&gl=IT&ceid=IT:it
Ogni ricerca dà ~100 articoli in ordine di Google (posizione 1 = più in alto). Si salva solo posizione, testata, titolo, ora e link.

Serve a tre cose:
  1. rete di sicurezza (rete/rete.py): una notizia in alto su Google (prime 30 USA, 15 Italia) di una testata FIDATA che da noi manca entra nel sito;
  2. classifica (premio_google, usato da pagine.py): una nostra notizia che Google mette in alto nelle ultime 24 ore sale un po';
  3. Breaking News ogni ora (ultimora.py): gli articoli delle testate fidate contano come le altre testate.
Tutte le testate che Google mostra (anche quelle non fidate) si annotano in testate.csv: nessuna fonte si butta.

  python3 ricerca_google.py CARTELLA      scarica le due ricerche e salva CARTELLA/AAAAMMGGHH.csv (ora UTC)
"""
import csv, datetime as dt, html, os, re, sys, urllib.parse, urllib.request
from email.utils import parsedate_to_datetime

QUI = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (AIgregatore; lettore di titoli e link)"}
RICERCHE = [("us", "artificial intelligence", "en-US", "US", "US:en"), ("it", "intelligenza artificiale", "it", "IT", "IT:it")]
CAMPI = ["ed", "pos", "sito", "titolo", "link", "data"]
POS_RETE = {"us": 30, "it": 15}  # rete di sicurezza: solo le prime 30 (USA) e 15 (Italia: più convegni e commenti generici)
ORE_PREMIO = 24       # classifica: le posizioni delle ultime 24 ore
TETTO = 2.5           # classifica: al massimo +2,5 «testate equivalenti»

NOMI = {"The Wall Street Journal": "Wall Street Journal", "WSJ": "Wall Street Journal", "The New York Times": "New York Times",
        "The Washington Post": "Washington Post", "Bloomberg.com": "Bloomberg", "WIRED": "Wired", "FT": "Financial Times",
        "Il Sole 24 ORE": "Il Sole 24 Ore", "La Repubblica": "la Repubblica", "AP": "AP News", "Associated Press": "AP News",
        "BBC": "BBC News", "CNBC.com": "CNBC", "Wired Italia": "Wired Italia", "WIRED Italia": "Wired Italia", "Rai News": "RaiNews",
        "Sky TG24": "Sky TG24", "TGCOM24": "Tgcom24", "Tgcom24": "Tgcom24", "Agi": "AGI", "Agenzia Nova": "Agenzia Nova"}
# testate di cui ci fidiamo (oltre alle nostre fonti): grandi giornali, agenzie, redazioni tecnologiche e scientifiche serie
FIDATE = {
    # USA e mondo
    "AP News", "Reuters", "Bloomberg", "Financial Times", "Wall Street Journal", "New York Times", "Washington Post", "The Economist",
    "The Atlantic", "Politico", "The Hill", "Fortune", "Forbes", "Business Insider", "Semafor", "Axios", "CNBC", "CNN", "NBC News",
    "CBS News", "ABC News", "NPR", "PBS", "The Guardian", "BBC News", "The Independent", "Nikkei Asia", "South China Morning Post",
    "Al Jazeera", "Newsweek", "USA Today", "Time", "Vox", "Los Angeles Times", "MarketWatch", "Barron's",  # Yahoo Finance no: ripubblica consigli di Borsa
    "The Globe and Mail", "Engadget", "VentureBeat", "Fast Company", "Gizmodo", "Mashable", "Tom's Hardware", "The Next Web",
    "9to5Mac", "9to5Google", "MacRumors", "CyberScoop", "The Record", "BleepingComputer", "Dark Reading", "SecurityWeek", "GeekWire",
    "Scientific American", "Nature", "Science", "New Scientist", "Quanta Magazine", "Futurism", "Computerworld", "CIO", "InfoWorld",
    "Platformer", "TechCrunch", "The Verge", "Wired", "Ars Technica", "MIT Technology Review", "IEEE Spectrum", "ZDNET", "The Register",
    "404 Media", "The Information", "SiliconANGLE", "CNET", "PCMag", "Tech Xplore", "Phys.org", "Rest of World", "Euronews",
    # Italia
    "ANSA", "AGI", "Adnkronos", "Agenzia Nova", "Il Post", "Wired Italia", "AI4Business", "Agenda Digitale", "HDblog", "DDay.it",
    "la Repubblica", "Corriere della Sera", "Il Sole 24 Ore", "La Stampa", "RaiNews", "Sky TG24", "Tgcom24", "Il Fatto Quotidiano",
    "Open", "Il Foglio", "Domani", "Internazionale", "Il Messaggero", "Il Giornale", "Avvenire", "Il Mattino", "il manifesto",
    "Milano Finanza", "Forbes Italia", "Fortune Italia", "StartupItalia", "Le Scienze", "Punto Informatico", "Tom's Hardware Italia",
    "Key4biz", "Formiche", "Corriere Comunicazioni", "ZeroUno", "Money.it", "Fanpage", "Euronews Italiano", "Il Resto del Carlino",
    "La Nazione", "Il Secolo XIX", "Corriere dell'Economia", "Italian Tech",
}


def nome(s):
    s = re.sub(r"\s+-\s+.*$", "", (s or "").strip()) or (s or "").strip()  # «ABC News - Breaking News, Latest News…» -> «ABC News»
    s = re.sub(r"^www\.", "", s)
    return NOMI.get(s, s)


def fidata(sito, nostre=()):
    n = nome(sito).lower()
    return n in {x.lower() for x in FIDATE} or n in {x.lower() for x in nostre}


def pulisci(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", x or ""))).strip()


def scarica():
    """Le due ricerche, in ordine di Google: [dict(ed, pos, sito, titolo, link, data)]"""
    out = []
    for ed, q, hl, gl, ceid in RICERCHE:
        u = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": hl, "gl": gl, "ceid": ceid})
        try: x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf-8", "replace")
        except Exception as e: print(f"Google News {ed}: {str(e)[:80]}"); continue
        for pos, it in enumerate(re.findall(r"<item>.*?</item>", x, re.S), 1):
            g = lambda p: (re.search(p, it, re.S) or [None, ""])[1]
            sito = nome(pulisci(g(r"<source[^>]*>(.*?)</source>")))
            t = pulisci(g(r"<title>(.*?)</title>")); t = re.sub(r"\s+-\s+[^-]+$", "", t)
            try: d = parsedate_to_datetime(g(r"<pubDate>(.*?)</pubDate>")).astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
            except Exception: d = ""
            link = re.sub(r"\?oc=\d+$", "", pulisci(g(r"<link>(.*?)</link>")))
            if t and sito: out.append(dict(ed=ed, pos=pos, sito=sito, titolo=t, link=link, data=d))
    return out


def foto(cartella, ora=None, righe=None, quante=100):
    """Scarica (o usa righe) e salva CARTELLA/AAAAMMGGHH.csv (le prime «quante» di ogni ricerca); tiene 8 giorni."""
    ora = ora or dt.datetime.now(dt.timezone.utc)
    righe = scarica() if righe is None else righe
    os.makedirs(cartella, exist_ok=True)
    if righe:
        with open(os.path.join(cartella, f"{ora:%Y%m%d%H}.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPI, extrasaction="ignore"); w.writeheader(); w.writerows(r for r in righe if int(r["pos"]) <= quante)
    lim = f"{ora - dt.timedelta(days=8):%Y%m%d%H}"
    for n in os.listdir(cartella):
        if re.fullmatch(r"\d{10}\.csv", n) and n[:10] < lim: os.remove(os.path.join(cartella, n))
    print(f"Google News: {sum(r['ed'] == 'us' for r in righe)} USA, {sum(r['ed'] == 'it' for r in righe)} Italia")
    return righe


# ---------------------------------------------------------------- per il giro completo (sito-auto)
FOTO = os.path.join(QUI, "foto")          # le foto dei giri completi + quelle orarie copiate dal repository del sito
ABB = os.path.join(QUI, "abbinati.csv")   # link di Google -> link del nostro articolo che racconta lo stesso fatto (rete.py)
ORE_URL = "https://raw.githubusercontent.com/manliograndi-del/manliograndi-del.github.io/main/.github/ricerche/google"


def leggi(f):
    return list(csv.DictReader(open(f, encoding="utf-8"))) if os.path.exists(f) else []


def copia_orarie(ora, ore=ORE_PREMIO + 2):
    """copia in foto/ le foto orarie fatte da GitHub (prima la copia locale del repository, poi internet)."""
    repo = os.path.join(os.environ.get("REPO_SITO", "/tmp/aigregatore-sito"), ".github", "ricerche", "google")
    os.makedirs(FOTO, exist_ok=True); n = []
    for h in range(ore, 0, -1):
        f = f"{ora - dt.timedelta(hours=h):%Y%m%d%H}.csv"; dest = os.path.join(FOTO, f)
        if os.path.exists(dest): continue
        try:
            dati = open(os.path.join(repo, f), "rb").read() if os.path.exists(os.path.join(repo, f)) else \
                urllib.request.urlopen(urllib.request.Request(f"{ORE_URL}/{f}", headers=UA), timeout=15).read()
            open(dest, "wb").write(dati); n.append(f[:10])
        except Exception: pass
    return n


def recenti(ora, ore=ORE_PREMIO):
    lim = f"{ora - dt.timedelta(hours=ore):%Y%m%d%H}"
    fs = sorted(f for f in os.listdir(FOTO) if re.fullmatch(r"\d{10}\.csv", f) and f[:10] >= lim) if os.path.isdir(FOTO) else []
    return [dict(r, foto=f[:10]) for f in fs for r in leggi(os.path.join(FOTO, f))]


def segna_testate(nostre=()):
    """testate.csv: tutte le testate che la ricerca di Google mostra, quante volte, in che posizione migliore, se fidate.
    Ogni foto si conta una volta sola (contate.txt)."""
    f = os.path.join(QUI, "testate.csv"); T = {(r["testata"], r["ed"]): r for r in leggi(f)}
    fc = os.path.join(QUI, "contate.txt"); fatte = set(open(fc).read().split()) if os.path.exists(fc) else set()
    nuove = sorted(n[:10] for n in os.listdir(FOTO) if re.fullmatch(r"\d{10}\.csv", n) and n[:10] not in fatte)
    righe = [dict(r, foto=n) for n in nuove for r in leggi(os.path.join(FOTO, n + ".csv"))]
    for r in righe:
        k = (r["sito"], r["ed"]); q = r.get("foto") or ""
        x = T.setdefault(k, dict(testata=r["sito"], ed=r["ed"], volte=0, migliore=999, prima=q, ultima=q, fidata="", nostra=""))
        x["volte"] = int(x["volte"]) + 1; x["migliore"] = min(int(x["migliore"]), int(r["pos"]))
        x["prima"] = min(x["prima"] or q, q); x["ultima"] = max(x["ultima"], q)
    for x in T.values():
        x["fidata"] = "sì" if fidata(x["testata"]) else "no"; x["nostra"] = "sì" if x["testata"].lower() in {n.lower() for n in nostre} else "no"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["testata", "ed", "volte", "migliore", "prima", "ultima", "fidata", "nostra"]); w.writeheader()
        w.writerows(sorted(T.values(), key=lambda x: (-int(x["volte"]), x["testata"])))
    lim = f"{dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=10):%Y%m%d%H}"
    open(fc, "w").write("\n".join(sorted(n for n in fatte | set(nuove) if n >= lim)) + "\n")
    return len(nuove)


_P = None
def premio_google(s):
    """Premio in «testate equivalenti» per la notizia s: posizione migliore su Google nelle ultime 24 ore, per ricerca.
    prime 10: +1,5 · 11-30: +1 · 31-100: +0,5; USA e Italia si sommano; tetto 2,5. Zero se non c'è."""
    global _P
    if _P is None:
        _P = {}
        try:
            ora = dt.datetime.now(dt.timezone.utc)
            A = {r["link_google"]: r["link_nostro"] for r in leggi(ABB) if r.get("link_nostro")}
            for r in recenti(ora):
                for l in {r["link"], A.get(r["link"], "")} - {""}:
                    k = (l, r["ed"]); _P[k] = min(_P.get(k, 999), int(r["pos"]))
        except Exception as e: print("google: premio saltato", str(e)[:100])
    best = {}
    for a in s.get("art", []):
        for ed in ("us", "it"):
            p = _P.get((a[2], ed))
            if p: best[ed] = min(best.get(ed, 999), p)
    v = sum(1.5 if p <= 10 else 1.0 if p <= 30 else 0.5 for p in best.values())
    return min(TETTO, v)


if __name__ == "__main__":
    foto(sys.argv[1] if len(sys.argv) > 1 else FOTO)
