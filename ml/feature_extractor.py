# ml/feature_extractor.py
import re
from urllib.parse import urlparse

SUSPICIOUS_KWS = ['login','verify','update','secure','account','bank','wallet','paypal','signin']
SUSPICIOUS_TLDS = ['zip','review','country','kim','cricket','link','work','party','gq','tk']


def extract_features(url: str):
    try:
        parsed = urlparse(url if re.match(r'^https?://', url) else 'http://' + url)
    except Exception:
        parsed = urlparse('http://' + url)

    host = parsed.netloc or parsed.path
    scheme = parsed.scheme.lower()

    has_https = 1 if scheme == 'https' else 0
    length = len(url)
    num_dots = host.count('.')
    contains_kw = int(any(kw in url.lower() for kw in SUSPICIOUS_KWS))
    tld = host.split('.')[-1].lower() if '.' in host else ''
    bad_tld = int(tld in SUSPICIOUS_TLDS)
    num_special = sum(1 for c in url if c in '/?=&%$@+')

    feats = {
        'has_https': has_https,
        'length': length,
        'num_dots': num_dots,
        'contains_kw': contains_kw,
        'bad_tld': bad_tld,
        'num_special': num_special,
        'tld': tld,
        'host': host,
    }
    return feats


def vectorize(feats: dict):
    return [
        feats['has_https'],
        feats['length'],
        feats['num_dots'],
        feats['contains_kw'],
        feats['bad_tld'],
        feats['num_special'],
    ]


def explain_features(feats: dict):
    reasons = []
    if not feats['has_https']:
        reasons.append('No HTTPS detected.')
    if feats['contains_kw']:
        reasons.append('Suspicious keyword present in URL.')
    if feats['bad_tld']:
        reasons.append('Suspicious top-level domain.')
    if feats['num_dots'] >= 3:
        reasons.append('Many subdomains (can hide real domain).')
    if feats['length'] > 75:
        reasons.append('Unusually long URL.')
    if feats['num_special'] >= 3:
        reasons.append('Many special query characters.')
    if not reasons:
        reasons.append('No strong red flags found.')
    return reasons

# # ml/feature_extractor.py
# import re
# from urllib.parse import urlparse


# SUSPICIOUS_KWS = ['login','verify','update','secure','account','bank','wallet','paypal','signin']
# SUSPICIOUS_TLDS = ['zip','review','country','kim','cricket','link','work','party','gq','tk']

# def extract_features(url: str):
#     try:
#         parsed = urlparse(url if re.match(r'^https?://', url) else 'http://' + url)
#     except Exception:
#         parsed = urlparse('http://' + url)

#     host = parsed.netloc or parsed.path
#     scheme = parsed.scheme.lower()

#     has_https = 1 if scheme == 'https' else 0
#     length = len(url)
#     num_dots = host.count('.')
#     contains_kw = int(any(kw in url.lower() for kw in SUSPICIOUS_KWS))
#     tld = host.split('.')[-1].lower() if '.' in host else ''
#     bad_tld = int(tld in SUSPICIOUS_TLDS)
#     num_special = sum(1 for c in url if c in '/?=&%$@+')

#     feats = {
#         'has_https': has_https,
#         'length': length,
#         'num_dots': num_dots,
#         'contains_kw': contains_kw,
#         'bad_tld': bad_tld,
#         'num_special': num_special,
#         'tld': tld,
#         'host': host,
#     }
#     return feats

# def vectorize(feats: dict):
#     return [
#         feats['has_https'],
#         feats['length'],
#         feats['num_dots'],
#         feats['contains_kw'],
#         feats['bad_tld'],
#         feats['num_special'],
#     ]

# def explain_features(feats: dict):
#     reasons = []
#     if not feats['has_https']:
#         reasons.append('No HTTPS detected.')
#     if feats['contains_kw']:
#         reasons.append('Suspicious keyword present in URL.')
#     if feats['bad_tld']:
#         reasons.append('Suspicious top-level domain.')
#     if feats['num_dots'] >= 3:
#         reasons.append('Many subdomains (can hide real domain).')
#     if feats['length'] > 75:
#         reasons.append('Unusually long URL.')
#     if feats['num_special'] >= 3:
#         reasons.append('Many special query characters.')
#     if not reasons:
#         reasons.append('No strong red flags found.')
#     return reasons
