#!/usr/bin/env python3
"""Publish only human-reviewed records; reject expired/incomplete evidence."""
import json,datetime
from pathlib import Path
r=Path(__file__).resolve().parents[1]; now=datetime.datetime.now(datetime.timezone.utc)
source=json.loads((r/'data/approved.json').read_text(encoding='utf8'))
out=[]
for x in source:
    try:
        if x['status']!='approved' or x['merchant_verified'] is not True:continue
        if not x['evidence_url'].startswith('https://') or not x['url'].startswith('https://'):continue
        reviewed=datetime.datetime.fromisoformat(x['reviewed_at'].replace('Z','+00:00'))
        priced=datetime.datetime.fromisoformat(x['priced_at'].replace('Z','+00:00'))
        if (now-reviewed).days>30 or (now-priced).total_seconds()>86400:continue
        if not all(x.get(k) for k in ('title','brand','sku','spec','merchant','platform','category')):continue
        if x['platform'] not in ('京东','天猫','拼多多'):continue
        price=float(x['price'])
        if price<=0:continue
        out.append({k:x[k] for k in ('title','brand','sku','spec','merchant','platform','category','url','priced_at')})
        out[-1]['price']=price
    except (KeyError,TypeError,ValueError,OverflowError):continue
(r/'data/products.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Published',len(out),'verified offers')
