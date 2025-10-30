DOMAIN_CODE = "networking_latency_analyzer"
def percentile(vals, p):
    if not vals: return 0
    vals = sorted(vals); k=(len(vals)-1)*p; f=int(k); c=min(f+1, len(vals)-1)
    if f==c: return vals[f]
    return vals[f] + (vals[c]-vals[f])*(k-f)
def analyze(payload):
    arr = [float(x) for x in payload.get("latencies_ms", []) if x is not None]
    if not arr: return {"domain":"networking_latency_analyzer","stats":{}}
    mean = sum(arr)/len(arr); p95 = percentile(arr,0.95); p99=percentile(arr,0.99)
    return {"domain":"networking_latency_analyzer","stats":{"count":len(arr),"mean_ms":round(mean,2),"p95_ms":round(p95,2),"p99_ms":round(p99,2)}}
