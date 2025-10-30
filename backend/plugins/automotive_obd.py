DOMAIN_CODE = "automotive_obd"
OBD={"P0300":"Random/Multiple Cylinder Misfire","P0171":"System Too Lean (Bank 1)","P0420":"Catalyst Efficiency Below Threshold","P0442":"EVAP small leak"}
def analyze(payload):
    codes=payload.get("codes", []); mapped=[{"code":c,"description":OBD.get(c,"Unknown")} for c in codes]; tips=[]
    if "P0171" in codes: tips.append("افحص تسريب هواء/MAF/ضغط الوقود")
    if "P0420" in codes: tips.append("تحقق من المحفّز الحفّاز وحساساته")
    return {"domain":"automotive_obd","inputs":payload,"codes":mapped,"suggestions":tips}
