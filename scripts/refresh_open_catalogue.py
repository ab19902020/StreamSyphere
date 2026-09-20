#!/usr/bin/env python3
"""Build the additional catalogue from publisher APIs and explicit item licences.

No media is downloaded. Each record retains source, creator and licence evidence.
Run manually and review data/open-catalogue.json before committing a refresh.
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import urllib.parse as up
import urllib.request as ur
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get('STREAMSPHERE_SOURCE_CACHE', str(ROOT.parent/'source-cache')))
CACHE.mkdir(parents=True, exist_ok=True)
HEADERS = {'User-Agent':'StreamSphereCatalogue/1.0 (https://github.com/ab19902020/StreamSyphere)'}
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
ISSUES = []
SOURCES = [
 {'id':'blender','name':'Blender Open Movies','website':'https://studio.blender.org/films/','rightsUrl':'https://studio.blender.org/remixing/','description':'Independent animated adventures and short films from Blender Studio.'},
 {'id':'archive-films','name':'Archive Open Cinema','website':'https://archive.org/details/feature_films','rightsUrl':'https://help.archive.org/help/rights/','description':'Classic films whose individual Archive records declare a public-domain or open licence.'},
 {'id':'prelinger','name':'Prelinger Archives','website':'https://archive.org/details/prelinger','rightsUrl':'https://archive.org/details/prelinger','description':'Historic documentaries, travel, industry and everyday life from the Prelinger collection.'},
 {'id':'nasa','name':'NASA Video Library','website':'https://images.nasa.gov/','rightsUrl':'https://www.nasa.gov/nasa-brand-center/images-and-media/','description':'Space, science and exploration series published by NASA.'},
 {'id':'jupiter','name':'Jupiter Broadcasting','website':'https://www.jupiterbroadcasting.com/show/','rightsUrl':'https://www.jupiterbroadcasting.com/show/','description':'Technology shows released by their publisher under Creative Commons BY-SA 4.0.'},
 {'id':'commons','name':'Wikimedia Commons Cinema','website':'https://commons.wikimedia.org/wiki/Category:Videos_of_films','rightsUrl':'https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia','description':'Historic and openly licensed films with file-level creator and licence credits.'},
 {'id':'official-live','name':'Official Live Channels','website':'https://www.youtube.com/','rightsUrl':'https://www.youtube.com/t/terms','description':'Broadcaster-published live players, with links back to the original channel.'},
]

def get(url, json_data=False):
    url=up.quote(url,safe=":/?=&%+[],@")
    path=CACHE/hashlib.sha256(url.encode()).hexdigest()
    if path.exists(): raw=path.read_bytes()
    else:
        if os.environ.get('STREAMSPHERE_CACHE_ONLY')=='1':raise RuntimeError('Not in this verified metadata snapshot')
        last=None
        for _ in range(1):
            try:
                with ur.urlopen(ur.Request(url,headers=HEADERS),timeout=12) as response: raw=response.read()
                path.write_bytes(raw);break
            except Exception as error:last=error
        else:raise last
    return json.loads(raw) if json_data else raw.decode('utf-8',errors='replace')

def clean(value, limit=700):
    if isinstance(value,list):value='; '.join(str(v) for v in value)
    value=html.unescape(re.sub('<[^>]+>',' ',str(value or '')))
    return re.sub(r'\s+',' ',value).strip()[:limit]

def url_https(value):
    return str(value).replace('http://','https://',1)

def licence(value):
    values=value if isinstance(value,list) else [value]
    for v in values:
        u=url_https(v or '').rstrip('/')+'/'
        if re.fullmatch(r'https://creativecommons.org/licenses/(by|by-sa)/(1\.0|2\.0|2\.5|3\.0|4\.0)/',u):
            kind,version=re.search(r'licenses/(by(?:-sa)?)/(\d\.\d)',u).groups()
            return {'name':f'CC {kind.upper()} {version}','url':u,'basis':'item licence'}
        if re.fullmatch(r'https://creativecommons.org/(publicdomain/(mark|zero)/1\.0|licenses/publicdomain)/',u):
            return {'name':'CC0 1.0' if '/zero/' in u else 'Public domain (source declaration)','url':u,'basis':'item declaration'}
    return None

def record(title,url,source,source_url,poster,description,creator,rights,genres,year=None,**extra):
    return dict(title=clean(title,180),url=url,sourceId=source,sourceUrl=source_url,poster=url_https(poster),description=clean(description) or clean(title),creator=clean(creator,180),rights=rights,genres=genres,year=year,checkedAt=TODAY,**extra)

def archive_search(collection, rows=100):
    # A collection's presence is not a licence. Every selected item is checked again below.
    params={'q':f'mediatype:movies AND collection:{collection} AND licenseurl:[* TO *]','fl[]':['identifier','title','licenseurl','year','creator','description'],'sort[]':'downloads desc','rows':rows,'output':'json'}
    d=get('https://archive.org/advancedsearch.php?'+up.urlencode(params,doseq=True),True)
    return d.get('response',{}).get('docs',[])

def archive_item(pair):
    source,doc=pair;ident=doc['identifier']
    try:
        meta=get('https://archive.org/metadata/'+up.quote(ident),True);m=meta.get('metadata',{});rights=licence(m.get('licenseurl'))
        if not rights or meta.get('is_dark') or 'access-restricted-item' in str(m.get('collection')):return None
        title=clean(m.get('title') or doc.get('title'))
        if re.search(r'(?i)\b(trailer|promo|batch|compilation|collection|porn|erotic|sexploitation)\b',title):return None
        # This lane is historic cinema, not recently uploaded commercial releases with doubtful tags.
        year_match=re.search(r'\b(18\d\d|19\d\d|20\d\d)\b',str(m.get('year') or m.get('date') or title))
        year=int(year_match[0]) if year_match else None
        if source=='archive-films' and (not year or year>1960):return None
        files=[f for f in meta.get('files',[]) if re.search(r'\.(mp4|webm|ogv)$',f.get('name',''),re.I) and not f.get('private')]
        if not files:return None
        rank={'h.264 ia':0,'h.264':1,'mpeg4':2,'512kb mpeg4':3,'webm':4,'ogg video':5}
        files.sort(key=lambda f:(rank.get(str(f.get('format','')).lower(),10),-int(f.get('size') or 0)))
        file=files[0]['name'];source_url='https://archive.org/details/'+up.quote(ident)
        description=clean(m.get('description')) or f'{title}. A film from the {"Prelinger Archives" if source=="prelinger" else "Internet Archive cinema collection"}.'
        return record(title,'archive:'+ident+'|'+file,source,source_url,'https://archive.org/services/img/'+up.quote(ident),description,m.get('creator') or m.get('publisher') or 'See source credits',rights,['Documentary' if source=='prelinger' else 'Classic cinema'],year,archiveId=ident,archiveFile=file)
    except Exception as e:ISSUES.append({'source':source,'item':ident,'error':str(e)});return None

def archives():
    candidates=[]
    for collection,source,count in [('feature_films','archive-films',180),('silent_films','archive-films',60),('prelinger','prelinger',40)]:
        try:candidates.extend((source,d) for d in archive_search(collection,count) if licence(d.get('licenseurl')))
        except Exception as e:ISSUES.append({'source':source,'error':str(e)})
    unique={d['identifier']:(s,d) for s,d in candidates}
    print('Archive candidates with explicit licences:',len(unique),flush=True)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:return [x for x in ex.map(archive_item,unique.values()) if x]

def attr(page,name):
    patterns=[rf'<meta[^>]+(?:property|name)=[\"\']{re.escape(name)}[\"\'][^>]+content=[\"\']([^\"\']*)',rf'<meta[^>]+content=[\"\']([^\"\']*)[\"\'][^>]+(?:property|name)=[\"\']{re.escape(name)}[\"\']']
    return next((html.unescape(m[1]) for p in patterns if (m:=re.search(p,page,re.I))), '')

def blender():
    slugs=['wing-it','charge','sprite-fright','coffee-run','spring','hero','dailydweebs','agent-327','caminandes-3','glass-half','cosmos-laundromat','caminandes-2','tears-of-steel','sintel','big-buck-bunny','elephants-dream']
    rights_page=get('https://studio.blender.org/remixing/')
    assert 'Creative Commons Attribution' in rights_page, 'Review Blender reuse policy before refreshing'
    print('Blender publisher reuse policy confirmed.',flush=True)
    def one(slug):
        try:
            u='https://studio.blender.org/projects/'+slug+'/'
            page=get(u);videos=re.findall(r'data-video="([^"]+)"',page)
            video=next((html.unescape(v) for v in videos if 'youtube.com/watch?' in v),None)
            if not video:return None
            video='https://www.youtube.com/watch?v='+up.parse_qs(up.urlparse(video).query)['v'][0]
            title=attr(page,'og:title').replace(' - Blender Studio','').strip()
            # Films are used intact through the publisher's embedded player; licence links remain visible.
            return record(title,video,'blender',u,attr(page,'og:image'),attr(page,'og:description') or attr(page,'description'),'Blender Studio / Blender Foundation',{'name':'CC BY (see film credits)','url':'https://studio.blender.org/remixing/','basis':'publisher permission'},['Animation','Short film'])
        except Exception as e:ISSUES.append({'source':'blender','item':slug,'error':str(e)})
    with cf.ThreadPoolExecutor(max_workers=4) as ex:return [x for x in ex.map(one,slugs) if x]

NASA_SHOWS=[('nasa-explorers','NASA Explorers','NASA Explorers'),('space-to-ground','Space to Ground','Space to Ground'),('nasa-sciencecasts','NASA ScienceCasts','ScienceCasts'),('this-week-nasa','This Week at NASA','This Week'),('nasa-x','NASA X','NASA X')]

def nasa():
    shows=[]
    for key,name,query in NASA_SHOWS:
        items=[]
        for page in range(1,16):
            try:
                data=get('https://images-api.nasa.gov/search?'+up.urlencode({'title':query,'media_type':'video','page_size':100,'page':page}),True)['collection']
                batch=data.get('items',[]);items.extend(batch)
                if len(batch)<100:break
            except Exception as e:ISSUES.append({'source':'nasa','item':name,'error':str(e)});break
        def one(item):
            try:
                m=item['data'][0];title=m['title'];description=m.get('description','')
                if query.lower() not in title.lower() or re.search(r'(?i)(?:teaser|trailer|b-?roll|promo)',title+' '+m['nasa_id']):return None
                if re.search(r'(?i)(?:copyright|©|all rights reserved|Universal Music|Getty Images|Shutterstock|Storyblocks)',description):return None
                if re.search(r'(?i)(?:music|footage|imagery)\s*(?:courtesy|provided|credit|by|:)',description):return None
                # Resolve the MP4 only when selected; indexing every episode stays lightweight.
                stream='nasa:'+m['nasa_id']
                poster=next((x['href'] for x in item.get('links',[]) if x.get('render')=='image'),'')
                if not poster:return None
                date=m.get('date_created','');match=re.search(r'\bS(\d+)\s*E(\d+)\b',title,re.I)
                episode=record(title,stream,'nasa','https://images.nasa.gov/details/'+up.quote(m['nasa_id']),poster,description,'NASA'+(' / '+m['center'] if m.get('center') else ''),{'name':'NASA media usage guidelines','url':'https://www.nasa.gov/nasa-brand-center/images-and-media/','basis':'publisher permission'},['Science','Documentary'],int(date[:4]) if date else None,publishedAt=date,assetManifest=url_https(item['href']))
                if match:episode.update(season=int(match[1]),episode=int(match[2]))
                else:episode['season']=int(date[:4]) if date else None
                return episode
            except Exception as e:ISSUES.append({'source':'nasa','item':item.get('href'),'error':str(e)})
        with cf.ThreadPoolExecutor(max_workers=6) as ex:episodes=[x for x in ex.map(one,items) if x]
        episodes=list({e['url']:e for e in episodes}.values());episodes.sort(key=lambda e:(e.get('publishedAt',''),e['title']))
        if episodes:
            shows.append({'id':key,'title':name,'sourceId':'nasa','poster':episodes[-1]['poster'],'description':f'{name}: science, engineering and space exploration from NASA’s own video library. Browse the available episodes by season or year.','episodes':episodes})
            print(name,len(episodes),'episodes',flush=True)
    return shows

def jupiter():
    try:
        raw=get('https://feeds2.feedburner.com/AllJupiterVideos');root=ET.fromstring(raw)
        items=root.findall('./channel/item');shows={}
        channel_image=root.find('./channel/{http://www.itunes.com/dtds/podcast-1.0.dtd}image').get('href')
        for item in items:
            title=clean(item.findtext('title'));enc=item.find('enclosure')
            if enc is None or not re.search(r'\.(mp4|webm)(?:\?|$)',enc.get('url','')):continue
            names=['LINUX Unplugged','Linux Action Show','Linux Action News','TechSNAP','BSD Now','Coder Radio','Jupiter EXTRAS','Self-Hosted','Unfilter','User Error','Ask Noah Show','Office Hours','Choose Linux','Tech Talk Today','The Friday Stream']
            show=next((n for n in names if n.lower() in title.lower()),None)
            if not show:
                for short,name in [('LUP','LINUX Unplugged'),('CR','Coder Radio'),('T3','Tech Talk Today'),('Ask Noah','Ask Noah Show')]:
                    if re.search(r'\b'+short+r'\s+\d+',title,re.I):show=name;break
            if not show:show='Jupiter EXTRAS'
            image=item.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}image');poster=image.get('href') if image is not None else ''
            if not poster:
                images=re.findall(r'<img[^>]+src=[\"\']([^\"\']+)',item.findtext('description') or '');poster=images[0] if images else ''
            if not poster:poster=channel_image
            e=record(title,url_https(enc.get('url')),'jupiter',item.findtext('link') or 'https://www.jupiterbroadcasting.com/',poster,item.findtext('description'),'Jupiter Broadcasting',{'name':'CC BY-SA 4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/','basis':'publisher permission'},['Technology'],publishedAt=item.findtext('pubDate') or '')
            date=__import__('email.utils',fromlist=['parsedate_to_datetime']).parsedate_to_datetime(item.findtext('pubDate'))
            e['publishedAt']=date.isoformat();e['year']=date.year;e['season']=date.year
            number=re.search(r'(?:LINUX Unplugged|Linux Action Show|TechSNAP|BSD Now|Coder Radio|Self-Hosted|Unfilter)\s*(\d+)',title,re.I)
            if number:e['episode']=int(number[1])
            shows.setdefault(show,[]).append(e)
        def series(pair):
            name,eps=pair;eps=list({e['url']:e for e in eps}.values());slug=re.sub('[^a-z]+','-',name.lower()).strip('-')
            poster=eps[0]['poster'];description='Technology conversations from Jupiter Broadcasting. Published under Creative Commons BY-SA 4.0.'
            try:
                page=get('https://www.jupiterbroadcasting.com/show/'+slug+'/')
                artwork=attr(page,'og:image')
                if artwork:poster=up.urljoin('https://www.jupiterbroadcasting.com/',artwork)
                description=attr(page,'og:description') or description
                for episode in eps:
                    if episode['poster']==channel_image:episode['poster']=poster
            except Exception:pass  # The feed's publisher artwork remains the fallback.
            return {'id':'jupiter-'+slug,'title':name,'sourceId':'jupiter','poster':poster,'description':clean(description),'episodes':list(reversed(eps))}
        with cf.ThreadPoolExecutor(max_workers=6) as ex:return list(ex.map(series,shows.items()))
    except Exception as e:ISSUES.append({'source':'jupiter','error':str(e)});return []

def commons():
    movies=[]
    for name in ['Georges Méliès','Alice Guy','Segundo de Chomón','Louis Feuillade','public domain full film']:
        try:
            params={'action':'query','generator':'search','gsrsearch':f'"{name}" filetype:video','gsrnamespace':6,'gsrlimit':50,'prop':'videoinfo','viprop':'url|size|extmetadata|derivatives','viurlwidth':400,'format':'json'}
            data=get('https://commons.wikimedia.org/w/api.php?'+up.urlencode(params),True)
            for page in data.get('query',{}).get('pages',{}).values():
                info=(page.get('videoinfo') or [{}])[0];ext=info.get('extmetadata',{})
                def field(k):return clean(ext.get(k,{}).get('value',''))
                lic=field('LicenseShortName');licurl=field('LicenseUrl')
                if lic=='Public domain':rights={'name':'Public domain (Commons declaration)','url':info['descriptionurl'],'basis':'file rights statement'}
                else:rights=licence(licurl)
                if not rights or float(info.get('duration',0))<180 or not info.get('thumburl'):continue
                if field('Restrictions'):continue
                choices=[d for d in info.get('derivatives',[]) if d.get('type','').startswith('video/webm') and int(d.get('height',0))>=360]
                choices.sort(key=lambda d:abs(int(d.get('height',0))-480))
                stream=choices[0]['src'] if choices else info.get('url')
                if not stream or not re.search(r'\.(webm|ogv)(?:\?|$)',stream):continue
                title=field('ObjectName') or re.sub(r'\.(webm|ogv)$','',page['title'].replace('File:',''),flags=re.I)
                year_match=re.search(r'\b(18\d\d|19\d\d)\b',field('DateTimeOriginal')+' '+page['title'])
                year=int(year_match[0]) if year_match else None
                if year and year>1940:continue
                movies.append(record(title,stream,'commons',info['descriptionurl'],info['thumburl'],field('ImageDescription') or f'{title}, an early cinema film preserved on Wikimedia Commons.',field('Artist') or name,rights,['Silent cinema','Short film'],year,duration=info.get('duration')))
        except Exception as e:ISSUES.append({'source':'commons','item':name,'error':str(e)})
    return movies

LIVE_PAGES=[
 ('France 24 · English','fr','English','https://www.france24.com/en/live'),
 ('France 24 · Français','fr','French','https://www.france24.com/fr/direct'),
 ('France 24 · العربية','fr','Arabic','https://www.france24.com/ar/'),
 ('France 24 · Español','fr','Spanish','https://www.france24.com/es/en-vivo'),
 ('Al Jazeera · العربية','qa','Arabic','https://www.aljazeera.net/live'),
 ('Al Jazeera · English','qa','English','https://www.aljazeera.com/live'),
]
def official_live():
    channels=[]
    for title,country,language,url in LIVE_PAGES:
        try:
            page=get(url)
            ids=re.findall(r'youtube(?:-nocookie)?\.com/embed/([a-zA-Z0-9_-]{11})(?:[^a-zA-Z0-9_-]|$)',page)
            if not ids:
                ids=re.findall(r'"(?:youtubeId|youtube_id|videoId)"\s*:\s*"([a-zA-Z0-9_-]{11})"',page)
            if not ids:continue
            vid=ids[0]
            channels.append(record(title,'https://www.youtube.com/watch?v='+vid,'official-live',url,'https://i.ytimg.com/vi/'+vid+'/hqdefault.jpg',f'{title} — the broadcaster’s live news player in {language}. Coverage and availability are controlled by the broadcaster.',title.split(' · ')[0],{'name':'Official YouTube embed','url':'https://www.youtube.com/t/terms','basis':'publisher embed'},['News'],country=country,language=language))
        except Exception as e:ISSUES.append({'source':'official-live','item':title,'error':str(e)})
    try:
        page=get('https://www.jupiterbroadcasting.com/live/')
        m=re.search(r'https://[^"<>\s]+\.m3u8',page)
        if m:
            channels.append(record('Jupiter Broadcasting Live',m[0],'jupiter','https://www.jupiterbroadcasting.com/live/','https://static.feedpress.com/logo/allvid-5f5bfb68c5c87.png','Technology programming from Jupiter Broadcasting. Live programmes and channel replays follow the publisher’s schedule.','Jupiter Broadcasting',{'name':'CC BY-SA 4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/','basis':'publisher permission'},['Technology'],country='us',language='English'))
    except Exception as e:ISSUES.append({'source':'jupiter-live','error':str(e)})
    return channels

def main():
    movies=[];shows=[];live=[]
    # Independent sources run concurrently; each provider has its own bounded queue.
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        tasks={ex.submit(archives):'archive',ex.submit(blender):'blender',ex.submit(nasa):'nasa',ex.submit(jupiter):'jupiter',ex.submit(commons):'commons',ex.submit(official_live):'live'}
        for task in cf.as_completed(tasks):
            name=tasks[task]
            try:
                rows=task.result()
                (live if name=='live' else shows if name in ('nasa','jupiter') else movies).extend(rows)
                print(name,'complete:',len(rows),flush=True)
            except Exception as e:ISSUES.append({'source':name,'error':str(e)})
    # Collapse duplicates within additions without conflating different years/remakes.
    unique={}
    for m in movies:
        key=(re.sub(r'[^a-z0-9]','',m['title'].lower()),m.get('year'))
        if key not in unique:unique[key]=m
    movies=list(unique.values())
    out={'schemaVersion':1,'updatedAt':TODAY,'sources':SOURCES,'movies':movies,'shows':shows,'live':live}
    if not movies or not shows or not live:raise RuntimeError('Incomplete refresh: keeping the previous catalogue. Review source failures before retrying.')
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/open-catalogue.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/open-catalogue-report.json').write_text(json.dumps({'updatedAt':TODAY,'movies':len(movies),'shows':len(shows),'episodes':sum(len(s['episodes']) for s in shows),'live':len(live),'issues':ISSUES},ensure_ascii=False,indent=2)+'\n')
    print('Saved',len(movies),'films,',len(shows),'shows,',sum(len(s['episodes']) for s in shows),'episodes;',len(ISSUES),'source issues.',flush=True)

if __name__=='__main__':main()
