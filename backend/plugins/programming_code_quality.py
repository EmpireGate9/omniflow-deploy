DOMAIN_CODE = "programming_code_quality"
def analyze(payload):
    files = payload.get("files", [])
    results=[]; total_loc=0; todos=0; fixmes=0
    for f in files:
        name=f.get("name",""); content=f.get("content","")
        lines=content.splitlines(); loc=len(lines)
        total_loc += loc
        t = sum(1 for L in lines if "TODO" in L); x = sum(1 for L in lines if "FIXME" in L)
        todos += t; fixmes += x
        avg_len = round(sum(len(L) for L in lines)/loc,2) if loc else 0
        results.append({"file":name,"loc":loc,"avg_line_len":avg_len,"todos":t,"fixmes":x})
    score = max(0, 100 - (todos*2 + fixmes*3))
    return {"domain":"programming_code_quality","summary":{"files":len(files),"total_loc":total_loc,"todos":todos,"fixmes":fixmes,"score":score},"details":results}
