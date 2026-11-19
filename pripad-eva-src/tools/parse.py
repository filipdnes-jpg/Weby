import re,json,sys
L=[l.strip() for l in open('edited.txt',encoding='utf8') if l.strip()]
out=[];sec='uvod';cnt={}
secmap={'Úvod':'uvod','A1':'a1','A2':'a2','A3':'a3','Spoločná časť – obálka':'obalka','B1':'b1','B2':'b2','B3':'b3','Spoločná časť – odchod':'odchod','Služba':'sluzba','Eva má problém':'pravda','Záver kapitoly':'zaver'}
for l in L[2:]:
    hit=[v for k,v in secmap.items() if l==k or l.startswith(k+' –') or l.startswith(k+' (')]
    if hit and not l.startswith(('NIKOL','EVA','BABKA')): sec=hit[0]; out.append({'t':'sec','id':sec}); continue
    m=re.match(r'^(NIKOL \(v duchu\)|NIKOL|EVA|BABKA)\s+(.*)$',l)
    if m:
        who={'NIKOL (v duchu)':'nikol_think','NIKOL':'nikol','EVA':'eva','BABKA':'babka'}[m[1]]
        cnt[sec]=cnt.get(sec,0)+1
        out.append({'t':'line','sec':sec,'id':f'k3_{sec}_{cnt[sec]:02d}','who':who,'text':m[2]});continue
    if l.startswith('▶'):
        q=l.split('–',1)[1].strip(); cnt[sec]=cnt.get(sec,0)+1
        out.append({'t':'choice','sec':sec,'id':f'k3_{sec}_q','who':'nikol_think','text':q});continue
    if l.startswith('-'): out.append({'t':'opt','text':l.lstrip('- ').strip()});continue
    if l.startswith('['): out.append({'t':'sfx','sec':sec,'text':l});continue
    out.append({'t':'?','text':l})
json.dump(out,open('script.json','w'),ensure_ascii=False,indent=1)
from collections import Counter
c=Counter((o['who']) for o in out if o['t'] in('line','choice')); print(c)
print(sum(len(re.sub(r'\[[^\]]*\]','',o['text'])) for o in out if o['t'] in('line','choice')),'chars')
print([o for o in out if o['t']=='?'])
