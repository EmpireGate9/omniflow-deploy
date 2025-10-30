import re
DOMAIN_CODE = "cybersecurity_indicator_scan"
IPV4 = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
DOMAIN = re.compile(r"\b([a-z0-9-]+\.)+[a-z]{2,}\b", re.I)
SHA256 = re.compile(r"\b[a-f0-9]{64}\b", re.I)
def analyze(payload):
    text = payload.get("text","")
    ips = sorted(set(IPV4.findall(text)))
    domains = sorted(set(DOMAIN.findall(text)))
    hashes = sorted(set(SHA256.findall(text)))
    return {"domain":"cybersecurity_indicator_scan","ioc":{"ipv4":ips,"domains":domains,"sha256":hashes}}
