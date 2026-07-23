#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_brvm.py — Rafraîchit BRVM Intelligence.

Usage :   python3 update_brvm.py
Effet  :   télécharge les derniers cours BRVM (dépôt public communautaire),
           recalcule les métriques, et réécrit les données dans
           brvm-intelligence.html (placé dans le même dossier).

Aucune dépendance externe (urllib + tarfile, standard library).
Pour enrichir les fondamentaux (PER, dividendes...) d'une nouvelle valeur :
éditez le dictionnaire REF ci-dessous.
"""
import urllib.request, tarfile, io, csv, os, json, re, sys
from datetime import datetime

REPO = "https://codeload.github.com/Fredysessie/brvm-data-public/tar.gz/refs/heads/main"
HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "brvm-intelligence.html")

# ---- Fondamentaux FY2025 (édite/complète ici) -------------------------------
PAYS_NOM = {"CI":"Côte d'Ivoire","SN":"Sénégal","BF":"Burkina Faso","TG":"Togo",
            "BJ":"Bénin","ML":"Mali","NE":"Niger","GW":"Guinée-Bissau"}
REF = {
 "SNTS":dict(nom="Sonatel",sec="Télécoms",pays="SN",conf=1,shares=100_000_000,net=413.6e9,div=1740,divg=42,rating="Strong Buy",note="Machine à cash : 48% marge EBITDA, 422 Md FCF, >20 ans de dividendes."),
 "ORAC":dict(nom="Orange CI",sec="Télécoms",pays="CI",conf=1,shares=144_500_000,rating="Accumuler",note="2e capi ; gros distributeur (~217 M$ versés)."),
 "ONTBF":dict(nom="Onatel (Moov)",sec="Télécoms",pays="BF",conf=1,rating="Hold",note="Télécom Burkina ; voix en érosion."),
 "ETIT":dict(nom="Ecobank ETI",sec="Banque",pays="TG",conf=1,shares=18_084_106_722,net=346e9,div=0.9052,equity=1598e9,rating="Accumuler",note="Deep value (~0,4x fonds propres). PBT record 801 M$. Risque Nigeria + report négatif."),
 "ECOC":dict(nom="Ecobank CI",sec="Banque",pays="CI",conf=1,rating="Hold"),
 "SGBC":dict(nom="Société Générale CI",sec="Banque",pays="CI",conf=1,rating="Hold",note="Bénéfice ~stable ; ~20% des volumes."),
 "SIBC":dict(nom="Société Ivoirienne de Banque",sec="Banque",pays="CI",conf=1,shares=100_000_000,net=57e9,div=330,rating="Accumuler",note="Qualité Attijariwafa, ×4 en 5 ans. S'est re-ratée."),
 "CBIBF":dict(nom="Coris Bank Int.",sec="Banque",pays="BF",conf=1,shares=32_000_000,net=65.5e9,div=900,divg=44,rating="Strong Buy",note="+36% bénéfice, AA, expansion CEMAC. Risque BF + IRVM 12,5%."),
 "NSBC":dict(nom="NSIA Banque CI",sec="Banque",pays="CI",conf=1,rating="Hold"),
 "BICC":dict(nom="BICICI",sec="Banque",pays="CI",conf=1,rating="Hold"),
 "BICB":dict(nom="BIIC Bénin",sec="Banque",pays="BJ",conf=1,rating="Hold"),
 "ORGT":dict(nom="Oragroup",sec="Banque",pays="TG",conf=1,rating="Watchlist",note="Redressement : H1 2025 +232%."),
 "BOAB":dict(nom="BOA Bénin",sec="Banque",pays="BJ",conf=1,rating="Hold"),
 "BOABF":dict(nom="BOA Burkina",sec="Banque",pays="BF",conf=1,rating="Hold",note="Bon rendement, cours accessible."),
 "BOAC":dict(nom="BOA Côte d'Ivoire",sec="Banque",pays="CI",conf=1,rating="Hold"),
 "BOAM":dict(nom="BOA Mali",sec="Banque",pays="ML",conf=1,rating="Hold"),
 "BOAN":dict(nom="BOA Niger",sec="Banque",pays="NE",conf=1,rating="Hold"),
 "BOAS":dict(nom="BOA Sénégal",sec="Banque",pays="SN",conf=1,rating="Hold"),
 "BNBC":dict(nom="Bernabé CI",sec="Distribution",pays="CI",conf=1,rating="Hold"),
 "CFAC":dict(nom="CFAO Motors CI",sec="Distribution",pays="CI",conf=1,rating="Hold"),
 "SHEC":dict(nom="Vivo Energy CI",sec="Énergie",pays="CI",conf=1,shares=63_000_000,net=6.03e9,div=85.07,divg=101,rating="Hold",note="⚠ Payout >100% (report à nouveau). Rdt ~4%."),
 "TTLC":dict(nom="TotalEnergies Mkt CI",sec="Énergie",pays="CI",conf=1,rating="Hold"),
 "TTLS":dict(nom="TotalEnergies Mkt SN",sec="Énergie",pays="SN",conf=1,rating="Hold"),
 "SMBC":dict(nom="SMB",sec="Énergie/Bitume",pays="CI",conf=1,rating="Hold"),
 "PALC":dict(nom="Palm CI",sec="Agro-industrie",pays="CI",conf=1,rating="Hold",note="Huile de palme, cyclique."),
 "SPHC":dict(nom="SAPH",sec="Agro (hévéa)",pays="CI",conf=1,rating="Hold",note="Caoutchouc, cyclique."),
 "SOGC":dict(nom="SOGB",sec="Agro (hévéa/palme)",pays="CI",conf=1,rating="Hold"),
 "SCRC":dict(nom="Sucrivoire",sec="Agro (sucre)",pays="CI",conf=1,rating="Hold",note="Forte hausse 2026 ; cyclique."),
 "NTLC":dict(nom="Nestlé CI",sec="Conso.",pays="CI",conf=1,rating="Hold"),
 "UNLC":dict(nom="Unilever CI",sec="Conso.",pays="CI",conf=1,rating="Hold"),
 "SLBC":dict(nom="Solibra",sec="Boissons",pays="CI",conf=1,rating="Hold",note="Brasserie, défensive, titre cher."),
 "STBC":dict(nom="SITAB",sec="Tabac",pays="CI",conf=1,rating="Avoid",note="⚠ Plus haut rendement MAIS rente tabac en déclin = piège à dividende."),
 "UNXC":dict(nom="Uniwax",sec="Textile",pays="CI",conf=1,rating="Hold",note="Pagne ; COIC a pris le contrôle."),
 "FTSC":dict(nom="Filtisac",sec="Industrie/Emballage",pays="CI",conf=1,rating="Hold",note="En forte baisse sur 1 an."),
 "CIEC":dict(nom="CIE",sec="Utilities (élec.)",pays="CI",conf=1,rating="Accumuler",note="Concession électricité, défensive, +118% bénéf. T1."),
 "LNBB":dict(nom="Loterie Nat. Bénin",sec="Jeux",pays="BJ",conf=1,rating="Hold",note="Marges sous pression en 2026."),
 "NEIC":dict(nom="NEI-CEDA",sec="Édition",pays="CI",conf=1,rating="Hold",note="Petite capi très volatile."),
 # à confirmer :
 "ABJC":dict(nom="Servair Abidjan",sec="Services",pays="CI",conf=0,rating="Hold",note="Résultats sous pression ; rdt ~3%."),
 "SDCC":dict(nom="SODECI",sec="Utilities (eau)",pays="CI",conf=0,rating="Accumuler",note="Concession eau, défensive. ⚠ vérifier ticker."),
 "SDSC":dict(nom="SODE / SODECI ?",sec="Utilities ?",pays="CI",conf=0,note="⚠ Ticker à confirmer."),
 "SAFC":dict(nom="SAFCA",sec="Finance",pays="CI",conf=0,note="⚠ À confirmer."),
 "SIVC":dict(nom="SIVOP ?",sec="Conso./Cosmét.",pays="CI",conf=0,note="⚠ À confirmer."),
 "STAC":dict(nom="SETAO ?",sec="BTP",pays="CI",conf=0,note="⚠ À confirmer."),
 "SEMC":dict(nom="Crown SIEM ?",sec="Industrie/Emballage",pays="CI",conf=0,note="⚠ À confirmer."),
 "CABC":dict(nom="SICABLE ?",sec="Industrie (câbles)",pays="CI",conf=0,note="⚠ À confirmer."),
 "SICC":dict(nom="SICOR ?",sec="Industrie",pays="CI",conf=0,note="⚠ Très illiquide ; à confirmer."),
 "SVOC":dict(nom="—",sec="?",pays="CI",conf=0,note="⚠ Ticker non identifié."),
 "PRSC":dict(nom="—",sec="?",pays="CI",conf=0,note="⚠ Ticker non identifié."),
}

BRVM_BASE = "https://www.brvm.org"

# Slugs brvm.org pour la page rapports (rapports-societe-cotes/{slug})
# Dérivés du site officiel ; compléter au besoin.
REPORT_SLUGS = {
    # Télécoms
    "SNTS":"sonatel","ORAC":"orange-ci","ONTBF":"onatel-bf",
    # Banques
    "ETIT":"ecobank-tg","ECOC":"ecobank-ci","SGBC":"sgci","SIBC":"sib",
    "CBIBF":"coris-bank-international","NSBC":"nsbc","BICC":"bici-ci","BICB":"biic",
    "ORGT":"oragroup",
    "BOAB":"bank-africa-bn","BOABF":"bank-africa-bf","BOAC":"bank-africa-ci",
    "BOAM":"bank-africa-ml","BOAN":"bank-africa-ng","BOAS":"bank-africa-sn",
    # Distribution / Industrie
    "BNBC":"bernabe-ci","CFAC":"cfao-motors-ci","SEMC":"crown-siem-ci",
    "CABC":"sicable","SICC":"sicor","FTSC":"filtisac-ci",
    # Énergie
    "SHEC":"vivo-energy-ci","TTLC":"total","TTLS":"totalenergies-marketing-sn","SMBC":"smb",
    # Agro-industrie
    "PALC":"palm-ci","SPHC":"saph-ci","SOGC":"sogb","SCRC":"sucrivoire",
    # Conso. / Services
    "NTLC":"nestle-ci","UNLC":"unilever-ci","SLBC":"solibra","STBC":"sitab",
    "UNXC":"uniwax-ci","ABJC":"servair-abidjan-ci","SAFC":"safca-ci",
    # Utilities
    "CIEC":"cie-ci","SDCC":"sodeci",
    # Autres
    "LNBB":"lnb","NEIC":"nei-ceda-ci","STAC":"setao-ci",
}

def fetch_company_reports(slug, max_docs=6):
    """Récupère les liens PDF de rapports depuis brvm.org pour un slug donné."""
    url = f"{BRVM_BASE}/fr/rapports-societe-cotes/{slug}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return []
    docs = []
    # Extrait tous les liens PDF (href absolu ou relatif vers /sites/default/files/)
    for m in re.finditer(
        r'href="((?:https?://www\.brvm\.org)?/sites/default/files/[^"]+\.pdf)"',
        html
    ):
        path = m.group(1)
        full_url = path if path.startswith("http") else BRVM_BASE + path
        fname = full_url.split("/")[-1]
        # Titre lisible à partir du nom de fichier
        title = fname.replace(".pdf","").replace("_"," ").strip()
        # Détecte le type
        fl = fname.lower()
        if "annuel" in fl or "annual" in fl:
            typ = "Rapport annuel"
        elif "semestre" in fl or "semestr" in fl or "-h1-" in fl or "-h2-" in fl:
            typ = "Semestriel"
        elif "trimest" in fl or "-q1-" in fl or "-q2-" in fl or "-q3-" in fl or "-q4-" in fl:
            typ = "Trimestriel"
        elif "etat" in fl or "financier" in fl:
            typ = "États financiers"
        else:
            typ = "Document"
        # Date : les 8 premiers chiffres du nom de fichier (YYYYMMDD)
        dm = re.match(r'^(\d{4})(\d{2})(\d{2})', fname)
        date = f"{dm.group(1)}-{dm.group(2)}-{dm.group(3)}" if dm else ""
        docs.append({"title": title[:80], "type": typ, "date": date,
                     "url": full_url})
    # Dédoublonnage par URL
    seen = set()
    out = []
    for d in docs:
        if d["url"] not in seen:
            seen.add(d["url"])
            out.append(d)
        if len(out) >= max_docs:
            break
    return out

def fetch_all_reports(tickers):
    """Scrape les rapports brvm.org pour tous les tickers connus."""
    reports = {}
    for tk in tickers:
        slug = REPORT_SLUGS.get(tk)
        if not slug:
            continue
        docs = fetch_company_reports(slug)
        if docs:
            reports[tk] = docs
    return reports

def fetch_repo():
    print("→ Téléchargement des données BRVM…")
    raw = urllib.request.urlopen(REPO, timeout=60).read()
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    files = {}
    for m in tf.getmembers():
        if m.name.endswith(".csv") or m.name.endswith("metadata.json"):
            files[m.name.split("/",1)[1]] = tf.extractfile(m).read().decode("utf-8","ignore")
    return files

def parse_csv(text):
    rows=[]
    for x in csv.DictReader(io.StringIO(text)):
        try: rows.append((x["Date"],float(x["Close"]),float(x["Volume"])))
        except: pass
    return rows

def metrics(rows):
    if not rows: return None
    date,close,_=rows[-1]; prev=rows[-2][1] if len(rows)>1 else close
    day=(close/prev-1)*100 if prev else 0
    def perf(s):
        sub=[r for r in rows if r[0]>=s]; return (close/sub[0][1]-1)*100 if sub else None
    l60=rows[-60:]; turn=sum(c*v for _,c,v in l60)/len(l60) if l60 else 0
    h=[c for _,c,_ in rows[-250:]]
    return dict(date=date,close=close,day=round(day,2),ytd=perf("2026-01-01"),
                y1=perf(f"{int(date[:4])-1}{date[4:]}"),turnover=round(turn),hi52=max(h),lo52=min(h))

def build(files):
    meta=json.loads(files["data/metadata.json"]); tickers=meta["tickers_list"]
    recs=[]
    for t in tickers:
        key=f"data/{t}/{t}.daily.csv"
        if key not in files: continue
        m=metrics(parse_csv(files[key]))
        if not m: continue
        r=REF.get(t,dict(nom=t,sec="?",pays="?",conf=0)); close=m["close"]
        shares=r.get("shares"); net=r.get("net"); div=r.get("div")
        cap=close*shares if shares else None
        pe=cap/net if (cap and net) else None
        pb=cap/r["equity"] if (cap and r.get("equity")) else None
        yld=div/close*100 if div else None
        recs.append(dict(tk=t,nom=r.get("nom",t),sec=r.get("sec","?"),pays=r.get("pays","?"),
            paysNom=PAYS_NOM.get(r.get("pays"),"—"),conf=r.get("conf",0),close=close,date=m["date"],
            day=m["day"],ytd=m["ytd"],y1=m["y1"],turnover=m["turnover"],hi52=m["hi52"],lo52=m["lo52"],
            cap=cap,pe=pe,pb=pb,yld=yld,payout=r.get("divg"),rating=r.get("rating"),note=r.get("note","")))
    def idx(t):
        k=f"data/{t}/{t}.daily.csv"; mm=metrics(parse_csv(files[k])) if k in files else None
        return dict(close=round(mm["close"],2),ytd=round(mm["ytd"],2) if mm["ytd"] else None) if mm else None
    indices={"Composite":idx("BRVMC"),"BRVM 30":idx("BRVM30"),"Prestige":idx("BRVMPR"),
             "Finance":idx("BRVMFI"),"Industrie":idx("BRVMIN"),"Total Return":idx("BRVMTR")}
    portf=[("SNTS",24),("CBIBF",17),("SIBC",15),("ORAC",12),("SDCC",10),("CIEC",10),("ETIT",8)]
    return dict(generated=datetime.now().strftime("%Y-%m-%d"),last_data=meta.get("last_updated"),
                source="Fredysessie/brvm-data-public",records=recs,indices=indices,portfolio=portf)

def build_history(files):
    """Historique compact : hebdo depuis 1998 + journalier sur 300 séances."""
    meta=json.loads(files["data/metadata.json"]); hist={}
    for t in meta["tickers_list"]:
        key=f"data/{t}/{t}.daily.csv"
        if key not in files: continue
        c=parse_csv(files[key])
        if not c: continue
        wk=[[c[i][0][2:].replace('-',''),round(c[i][1])] for i in range(0,len(c),5)]
        if wk and wk[-1][0]!=c[-1][0][2:].replace('-',''): wk.append([c[-1][0][2:].replace('-',''),round(c[-1][1])])
        dl=[[r[0][2:].replace('-',''),round(r[1])] for r in c[-300:]]
        hist[t]={"w":wk,"d":dl}
    return hist

def swap(html, name, value, end_anchor):
    """Remplace `const <name> = ...;` jusqu'à l'ancre suivante."""
    head=html.split(f"const {name} = ")[0]
    tail=html.split(end_anchor,1)[1]
    return head+f"const {name} = "+value+";\n"+end_anchor+tail

def main():
    if not os.path.exists(HTML):
        sys.exit("brvm-intelligence.html introuvable dans ce dossier. Place ce script à côté du fichier HTML.")
    files=fetch_repo()
    snap=build(files)
    tickers=[r["tk"] for r in snap["records"]]
    print("→ Récupération des rapports brvm.org…")
    reports=fetch_all_reports(tickers)
    print(f"  {len(reports)} sociétés avec rapports trouvés.")
    html=open(HTML,encoding="utf-8").read()
    has_hist = "const HISTORY = " in html
    has_rep  = "const REPORTS = " in html
    # Ordre des ancres dans le HTML : DATA → HISTORY → REPORTS → EUR
    next_after_data = "const HISTORY = " if has_hist else ("const REPORTS = " if has_rep else "const EUR")
    html=swap(html,"DATA",json.dumps(snap,ensure_ascii=False,separators=(',',':')), next_after_data)
    if has_hist:
        hist=build_history(files)
        next_after_hist = "const REPORTS = " if has_rep else "const EUR"
        html=swap(html,"HISTORY",json.dumps(hist,ensure_ascii=False,separators=(',',':')), next_after_hist)
    if has_rep:
        html=swap(html,"REPORTS",json.dumps(reports,ensure_ascii=False,separators=(',',':')),"const EUR")
    open(HTML,"w",encoding="utf-8").write(html)
    print(f"✓ Mis à jour. {len(snap['records'])} valeurs · cours au {snap['records'][0]['date']} · "
          f"Composite {snap['indices']['Composite']['close']} ({snap['indices']['Composite']['ytd']:+.1f}% YTD)"
          + (" · historique graphiques rafraîchi" if has_hist else "")
          + (f" · {len(reports)} rapports intégrés" if reports else ""))

if __name__=="__main__":
    main()
