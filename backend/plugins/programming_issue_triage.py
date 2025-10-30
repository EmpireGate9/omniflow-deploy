DOMAIN_CODE = "programming_issue_triage"
def analyze(payload):
    title=(payload.get("title") or "").lower(); body=(payload.get("body") or "").lower()
    text=title+"\n"+body
    labels=set(); priority="P3"
    if any(k in text for k in ["security","漏洞","xss","csrf","sql injection"]): labels.add("security"); priority="P0"
    if any(k in text for k in ["crash","panic","fatal","exception"]): labels.add("bug"); priority="P0"
    if any(k in text for k in ["performance","slow","latency"]): labels.add("performance"); priority="P1"
    if any(k in text for k in ["feature","enhancement","improvement"]): labels.add("feature")
    area=[]; 
    if "ui" in text or "ux" in text: area.append("ui/ux")
    if "api" in text: area.append("api")
    if "db" in text or "database" in text: area.append("database")
    if "mobile" in text: area.append("mobile")
    return {"domain":"programming_issue_triage","labels": sorted(labels), "priority": priority, "areas": area or ["general"]}
