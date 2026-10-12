#!/usr/bin/env python3
"""Conservative public-page collector: robots checks, no login/captcha bypass, no auto-approval."""
import json, re, time, urllib.request, urllib.parse, urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Metadata(HTMLParser):
    def __init__(self): super().__init__();self.scripts=[];self.active=False;self.buf=[];self.meta={}
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='script' and d.get('type','').lower()=='application/ld+json':self.active=True;self.buf=[]
        if tag=='meta' and d.get('property','').startswith('og:'):self.meta[d['property']]=d.get('content','')
    def handle_data(self,data):
        if self.active:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.active:self.scripts.append(''.join(self.buf));self.active=False

def products_from(data):
    if isinstance(data,list):
        for x in data:yield from products_from(x)
    elif isinstance(data,dict):
        typ=data.get('@type',[]);typ=[typ] if isinstance(typ,str) else typ
        if 'Product' in typ:yield data
        for k in ('@graph','mainEntity','itemListElement'):
            if k in data:yield from products_from(data[k])

def collect(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('只支持公开 HTTPS 商品页面')
    origin=f'{u.scheme}://{u.netloc}'
    rp=urllib.robotparser.RobotFileParser();rp.set_url(origin+'/robots.txt')
    try:rp.read()
    except Exception as exc:raise RuntimeError('无法检查 robots.txt，跳过') from exc
    ua='TongjiaYouxuanResearchBot/0.1 (manual review; contact via repository issues)'
    if not rp.can_fetch(ua,url):raise PermissionError('robots.txt 不允许抓取')
    req=urllib.request.Request(url,headers={'User-Agent':ua,'Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=12) as resp:
        if urllib.parse.urlsplit(resp.url).hostname!=u.hostname:raise RuntimeError('页面发生跨域跳转，跳过')
        if 'text/html' not in resp.headers.get('Content-Type',''):raise ValueError('不是 HTML 页面')
        body=resp.read(1_000_001)
        if len(body)>1_000_000:raise ValueError('页面过大')
        charset=resp.headers.get_content_charset() or 'utf-8'
    parser=Metadata();parser.feed(body.decode(charset,errors='replace'))
    found=[]
    for raw in parser.scripts:
        try:
            for prod in products_from(json.loads(raw)):
                offers=prod.get('offers',{});offers=offers[0] if isinstance(offers,list) and offers else offers
                offers=offers if isinstance(offers,dict) else {}
                found.append({'title':str(prod.get('name',''))[:250], 'brand':str(prod.get('brand',{}).get('name','') if isinstance(prod.get('brand'),dict) else prod.get('brand',''))[:120], 'price':str(offers.get('price',''))[:40], 'currency':str(offers.get('priceCurrency',''))[:12], 'image':prod.get('image',''), 'sku':str(prod.get('sku',''))[:100]})
        except (ValueError,TypeError):pass
    return {'url':url,'platform':u.hostname,'collected_at':datetime.now(timezone.utc).isoformat(),'candidates':found,'review_status':'pending','merchant_verified':False,'note':'结构化数据未必提供真实到手价；人工核验店铺主体、商品规格及价格'}

def main():
    urls=[s.strip() for s in (ROOT/'data/urls.txt').read_text(encoding='utf8').splitlines() if s.strip() and not s.lstrip().startswith('#')]
    records=[]
    for url in urls[:20]:
        try:records.append(collect(url));print('OK',url)
        except Exception as exc:records.append({'url':url,'review_status':'error','reason':str(exc)});print('SKIP',url,str(exc))
        time.sleep(2)
    (ROOT/'data/candidates.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('已输出待审核候选数据；没有自动认定官方店铺。')
if __name__=='__main__':main()
