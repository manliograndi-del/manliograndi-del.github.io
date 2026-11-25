# -*- coding: utf-8 -*-
"""AIgregatore · cosa cerca la gente NELLE ULTIME ORE (R26, chiesto da Manlio il 25/11/2026). Zero token, nessuna IA.

Gira ogni ora nell'aggiornamento gratuito di GitHub (insieme alla Breaking News) e salva un file piccolo per ogni ora:
  wiki/AAAAMMGGHH.csv  visite Wikipedia di quell'ora (inglese e italiano, computer + telefono), solo pagine utili:
                       pagine sull'AI, protagonisti noti e le 300 pagine inglesi più viste dell'ora.
                       Fonte: dumps.wikimedia.org/other/pageviews (file pubblico ogni ora, pronto con 3-5 ore di ritardo).
                       Recupera da solo le ore mancanti delle ultime 30 (al massimo 4 per volta).
  sugg/AAAAMMGGHH.csv  i suggerimenti di Google (quello che Google propone mentre scrivi) per ~30 parole AI, Italia e USA.
                       Una voce che compare all'improvviso = ricerca che sta salendo adesso.
Tiene 8 giorni, poi cancella. Il giro completo (interesse.py) legge questi file e li trasforma in punti per le notizie.
Uso: python3 ricerche_ore.py CARTELLA   (es. .github/ricerche)
"""
import csv, datetime as dt, gzip, heapq, io, json, os, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "AIgregatore/0.1 (lettore di notizie; poche richieste)"}
TENGO_GIORNI = 8
AI = re.compile(r"(?i)(?:^|[_(])(?:AI|A\.I\.|IA|AGI|LLM|GPT[-\w.]*)(?:$|[_),])|chatgpt|openai|anthropic|claude_\(|gemini_\(|google_gemini|grok|copilot|llama_\(|mistral_ai|deepseek|nvidia"
                r"|artificial_intelligence|intelligenza_artificiale|machine_learning|apprendimento_automatico|deep_learning|neural_network|rete_neurale"
                r"|language_model|chatbot|altman|amodei|hassabis|deepmind|perplexity|midjourney|sora_\(|qwen|hugging_face|kimi_|moonshot_ai|superintelligen"
                r"|xai_\(|cursor_\(|generative|transformer_\(|agentic|ai_agent|stargate_llc|sutskever|karpathy|lecun|hinton|jensen_huang|zuckerberg|musk")
SEGUI = {"OpenAI", "ChatGPT", "Sam_Altman", "Anthropic", "Claude_(AI)", "Dario_Amodei", "Gemini_(chatbot)", "Google_DeepMind", "Demis_Hassabis", "Nvidia",
         "Jensen_Huang", "Meta_AI", "Mark_Zuckerberg", "Microsoft_Copilot", "Satya_Nadella", "Siri", "Apple_Intelligence", "Qwen", "Perplexity_AI", "Mistral_AI",
         "Grok_(chatbot)", "XAI_(company)", "DeepSeek", "Midjourney", "Hugging_Face", "Elon_Musk", "Sundar_Pichai", "Tim_Cook", "Microsoft", "Google", "Apple_Inc.", "Meta_Platforms"}
SEMI = {"US": ["chatgpt", "openai", "claude", "anthropic", "gemini", "google ai", "grok", "copilot", "meta ai", "nvidia", "deepseek", "perplexity",
               "sora", "llama", "mistral", "sam altman", "ai", "ai news", "ai model", "gpt"],
        "IT": ["chatgpt", "openai", "claude", "gemini", "intelligenza artificiale", "ia", "grok", "copilot", "deepseek", "nvidia", "meta ai", "perplexity"]}


def get(u, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout)


def wiki_ora(ora, cartella):
    """scarica il file Wikipedia di quell'ora; False se non è ancora pronto"""
    u = f"https://dumps.wikimedia.org/other/pageviews/{ora:%Y}/{ora:%Y-%m}/pageviews-{ora:%Y%m%d-%H}0000.gz"
    try: r = get(u, 120)
    except Exception as e:
        if "404" in str(e): return False
        raise
    V, top = {}, {}
    with gzip.open(r, "rt", encoding="utf-8", errors="replace") as fh:
        for riga in fh:
            dom = riga[:5]
            if not (dom.startswith("en ") or dom.startswith("en.m ") or dom.startswith("it ") or dom.startswith("it.m ")): continue
            p = riga.split(" ")
            if len(p) < 3 or p[0] not in ("en", "en.m", "it", "it.m"): continue
            k = (p[0][:2], p[1]); V[k] = V.get(k, 0) + int(p[2])
    tieni = {k: v for k, v in V.items() if v >= 3 and (k[1] in SEGUI or AI.search(k[1]))}
    en = [(v, k) for k, v in V.items() if k[0] == "en" and ":" not in k[1] and k[1] not in ("Main_Page", "-")]
    for v, k in heapq.nlargest(300, en): tieni[k] = v
    os.makedirs(os.path.join(cartella, "wiki"), exist_ok=True)
    with open(os.path.join(cartella, "wiki", f"{ora:%Y%m%d%H}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["lingua", "pagina", "visite"])
        for (l, pg), v in sorted(tieni.items(), key=lambda kv: -kv[1]): w.writerow([l, pg, v])
    return True


def wikipedia(cartella, adesso, massimo=4):
    fatti = 0
    for h in range(30, 0, -1):  # dalla più vecchia mancante alla più recente
        ora = (adesso - dt.timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
        if os.path.exists(os.path.join(cartella, "wiki", f"{ora:%Y%m%d%H}.csv")): continue
        if fatti >= massimo: break
        try:
            ok = wiki_ora(ora, cartella)
        except Exception as e: print("wikipedia", ora, str(e)[:100]); break
        if not ok:
            if h <= 8: break  # le ore recenti non sono ancora pronte
            continue
        fatti += 1; print("wikipedia: ora", f"{ora:%d/%m %H}:00 UTC")


def suggerimenti(cartella, adesso):
    righe = []
    for paese, semi in SEMI.items():
        hl = "it" if paese == "IT" else "en"
        for s in semi:
            u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(dict(client="firefox", hl=hl, gl=paese.lower(), ie="utf-8", oe="utf-8", q=s))
            try:
                d = json.loads(get(u, 20).read().decode("utf-8", "replace"))
                tipi = (d[3] if len(d) > 3 and isinstance(d[3], dict) else {}).get("google:suggestsubtypes", [])
                for i, x in enumerate(d[1]): righe.append([paese, s, i + 1, x, ".".join(map(str, tipi[i])) if i < len(tipi) else ""])
            except Exception as e:
                print("suggerimenti", paese, s, str(e)[:80])
                if "429" in str(e): break
            time.sleep(1)
    if not righe: return
    os.makedirs(os.path.join(cartella, "sugg"), exist_ok=True)
    with open(os.path.join(cartella, "sugg", f"{adesso:%Y%m%d%H}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["paese", "seme", "posizione", "suggerimento", "tipo"]); w.writerows(righe)
    print("suggerimenti:", len(righe))


def pulisci(cartella, adesso):
    lim = f"{adesso - dt.timedelta(days=TENGO_GIORNI):%Y%m%d%H}"
    for sotto in ("wiki", "sugg"):
        d = os.path.join(cartella, sotto)
        for f in (os.listdir(d) if os.path.isdir(d) else []):
            if f[:10] < lim: os.remove(os.path.join(d, f))


if __name__ == "__main__":
    cartella = sys.argv[1] if len(sys.argv) > 1 else "ricerche"
    adesso = dt.datetime.now(dt.timezone.utc)
    try: suggerimenti(cartella, adesso)
    except Exception as e: print("suggerimenti saltati:", e)
    try: wikipedia(cartella, adesso, int(sys.argv[2]) if len(sys.argv) > 2 else 4)
    except Exception as e: print("wikipedia saltata:", e)
    pulisci(cartella, adesso)
