try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    SPACY_OK = True
except Exception as _:
    SPACY_OK = False
    nlp = None
# imports lol
import sys
import csv
import json
import re

# regex stuff (copied from stackoverflow)
phone_re = re.compile(r'\b(\d{10})\b')
aadhar_re = re.compile(r'\b(\d{4}\s?\d{4}\s?\d{4})\b')
passport_re = re.compile(r'\b([A-PR-WYa-pr-wy][1-9]\d{6})\b')
upi_re = re.compile(r'\b[\w.-]+@[\w.-]+\b')
email_re = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
ip_re = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
addr_re = re.compile(r'\d+\s+\w+.*\d{6}')

# masking functions (so cool)
def phmask(p):
    return p[:2] + 'XXXXXX' + p[-2:]
def amask(a):
    return a[:2] + 'XXXXXXXX' + a[-2:]
def pmask(p):
    return p[0] + 'XXXXXXX'
def emask(e):
    x = e.split('@')
    if len(x[0]) > 2:
        return x[0][:2] + 'XXX' + '@' + x[1]
    return 'X'*len(x[0]) + '@' + x[1]
def nmask(n):
    # lol names
    return ' '.join([i[0]+'XXX' if len(i)>1 else i for i in n.split()])
def upimask(u):
    user, dom = u.split('@')
    if len(user)>2:
        return user[:2]+'XXX@'+dom
    return 'X'*len(user)+'@'+dom
def adrmask(a):
    return '[REDACTED_PII]'
def ipmask(ip):
    return ip.split('.')[0]+'.XXX.XXX.'+ip.split('.')[-1]

def isname(n):
    return len(n.split())>=2
def isaddr(a):
    return bool(addr_re.search(a))

def detect(record):
    # this is the main thing
    found = False
    combi = set()
    red = record.copy()
    # phone
    if 'phone' in record and phone_re.fullmatch(str(record['phone'])):
        found = True
        red['phone'] = phmask(str(record['phone']))
    # aadhar
    if 'aadhar' in record and aadhar_re.fullmatch(str(record['aadhar']).replace(' ', '')):
        found = True
        red['aadhar'] = amask(str(record['aadhar']).replace(' ', ''))
    # passport
    if 'passport' in record and passport_re.fullmatch(str(record['passport'])):
        found = True
        red['passport'] = pmask(str(record['passport']))
    # upi
    if 'upi_id' in record and upi_re.fullmatch(str(record['upi_id'])):
        found = True
        red['upi_id'] = upimask(str(record['upi_id']))
    # name
    if 'name' in record and isname(str(record['name'])):
        combi.add('name')
        red['name'] = nmask(str(record['name']))
    # email
    if 'email' in record and email_re.fullmatch(str(record['email'])):
        combi.add('email')
        red['email'] = emask(str(record['email']))
    # addr
    if 'address' in record and isaddr(str(record['address'])):
        combi.add('address')
        red['address'] = adrmask(str(record['address']))
    # ip
    if 'ip_address' in record and ip_re.fullmatch(str(record['ip_address'])):
        combi.add('ip')
        red['ip_address'] = ipmask(str(record['ip_address']))
    # device
    if 'device_id' in record and len(str(record['device_id']))>6:
        combi.add('device')
        red['device_id'] = '[REDACTED_PII]'
    # --- Hybrid: NER for unstructured fields ---
    # Only run if spaCy is available
    unstructured_keys = ['product_description', 'query_type', 'search_query', 'filters', 'issue', 'notes', 'comments']
    if SPACY_OK:
        for k in unstructured_keys:
            if k in record and isinstance(record[k], str) and record[k].strip():
                doc = nlp(record[k])
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'GPE', 'ORG', 'LOC', 'ADDRESS', 'EMAIL', 'CARDINAL']:
                        # Mask the entity in the text
                        red[k] = record[k].replace(ent.text, '[REDACTED_PII]')
                        found = True
    else:
        if not hasattr(detect, '_spacy_warned'):
            print('spaCy not installed or en_core_web_sm not available. NER will be skipped.')
            detect._spacy_warned = True

    # logic (teacher said this is important)
    if len(combi)>=2:
        found = True
    if len(combi)==1 and not found:
        for k in combi:
            if k=='name': red['name']=record['name']
            if k=='email': red['email']=record['email']
            if k=='address': red['address']=record['address']
            if k=='ip': red['ip_address']=record['ip_address']
            if k=='device': red['device_id']=record['device_id']
    return red, found

def main():
    # main function (pls work)
    if len(sys.argv)!=2:
        print('Usage: python3 detector_eeshaan_undar_bhat.py <input_csv>')
        sys.exit(1)
    inp = sys.argv[1]
    outp = 'redacted_output_eeshaan_undar_bhat.csv'
    with open(inp, newline='', encoding='utf-8') as f, open(outp, 'w', newline='', encoding='utf-8') as g:
        rdr = csv.DictReader(f)
        flds = ['record_id', 'redacted_data_json', 'is_pii']
        wtr = csv.DictWriter(g, fieldnames=flds)
        wtr.writeheader()
        for row in rdr:
            rid = row['record_id']
            # Accept both Data_json and data_json for robustness
            djs = row.get('Data_json') or row.get('data_json')
            if not djs:
                print('No data_json/Data_json for record_id', rid)
                continue
            if djs.startswith('"') and djs.endswith('"'):
                djs = djs[1:-1]
            djs = djs.replace('""', '"')
            def auto_fix_json(s):
                # Add quotes around unquoted values (dates, words, pending, etc.)
                import re
                # Fix date values: key: YYYY-MM-DD or YYYY/MM/DD or YYYY.MM.DD
                s = re.sub(r'(:\s*)(\d{4}[-/.]\d{2}[-/.]\d{2})([\s,}])', r'\1"\2"\3', s)
                # Fix unquoted words (e.g., pending, approved, etc.)
                s = re.sub(r'(:\s*)([a-zA-Z_][a-zA-Z0-9_]*)([\s,}])', r'\1"\2"\3', s)
                return s
            try:
                try:
                    dj = json.loads(djs)
                except Exception:
                    # Try auto-fix
                    fixed = auto_fix_json(djs)
                    dj = json.loads(fixed)
            except Exception as e:
                print('Error parsing JSON for record_id', rid, ':', e, '\nString:', djs)
                continue
            red, ispii = detect(dj)
            wtr.writerow({
                'record_id': rid,
                'redacted_data_json': json.dumps(red, ensure_ascii=False),
                'is_pii': str(ispii)
            })
    print('Output written to', outp)

if __name__=='__main__':
    main()
