DOMAIN_CODE = "construction"
def analyze(payload):
    area=float(payload.get("site_area_m2",0)); floors=int(payload.get("floors",1))
    structure=(payload.get("structure") or "rc").lower(); finish=(payload.get("finish_level") or "standard").lower()
    total=area*floors
    if total<=0: raise ValueError("site_area_m2 must be > 0")
    unit_cost={"rc":350,"steel":300}.get(structure,350); addon={"basic":0,"standard":80,"premium":160}.get(finish,80)
    cost=(unit_cost+addon)*total; cement=round(0.08*total,2); steel=round(0.05*total,2); blocks=int(12*total); days=int(45+total/20)
    return {"domain":"construction","inputs":payload,"estimates":{"total_area_m2":total,"materials":{"cement_tons":cement,"steel_tons":steel,"blocks_units":blocks},"duration_days":days,"cost_estimate":round(cost,2)}}
