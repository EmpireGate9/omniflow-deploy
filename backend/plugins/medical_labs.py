DOMAIN_CODE = "medical_labs"
def analyze(payload):
    labs = payload.get("labs", [])
    res=[]; alerts=0
    for x in labs:
        name=x.get("name"); val=float(x.get("value")); lo=float(x.get("ref_low")); hi=float(x.get("ref_high")); unit=x.get("unit","")
        status="normal"
        if val<lo: status="low"; alerts+=1
        elif val>hi: status="high"; alerts+=1
        res.append({"name":name,"value":val,"unit":unit,"range":[lo,hi],"status":status})
    return {"domain":"medical_labs","summary":{"total":len(labs),"alerts":alerts},"results":res,"disclaimer":"تعليمي فقط، ليس تشخيصًا"}
