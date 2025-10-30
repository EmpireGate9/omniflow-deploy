DOMAIN_CODE = "data_etl_validator"
def analyze(payload):
    schema = payload.get("schema", {})
    fields = [f.get("name") for f in schema.get("fields", [])]
    required = [f.get("name") for f in schema.get("fields", []) if f.get("required")]
    records = payload.get("records", [])
    errors = []
    for i, r in enumerate(records):
        miss = [req for req in required if req not in r or r.get(req) in (None, "")]
        if miss: errors.append({"row": i, "missing": miss})
    return {"domain":"data_etl_validator","summary":{"records":len(records),"errors":len(errors)},"errors":errors,"fields":fields}
