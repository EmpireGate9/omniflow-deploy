DOMAIN_CODE = "devops_log_parser"
def analyze(payload):
    log = payload.get("log_text",""); lines = log.splitlines()
    errors = [L for L in lines if "ERROR" in L or "Error" in L]
    warns  = [L for L in lines if "WARN" in L or "Warning" in L]
    top={}
    for e in errors:
        k=e.strip()[:120]; top[k]=top.get(k,0)+1
    top_list = sorted(top.items(), key=lambda x: x[1], reverse=True)[:10]
    return {"domain":"devops_log_parser","counts":{"lines":len(lines),"errors":len(errors),"warnings":len(warns)},"top_errors":[{"line":k,"count":v} for k,v in top_list]}
