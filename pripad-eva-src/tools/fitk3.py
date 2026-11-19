import json
from subfit import segs, fit
A='/home/claude/site/a/'
def L(w,t): return {'who':w,'text':t}
E=lambda t:L('eva',t); N=lambda t:L('nikol',t); T=lambda t:L('nikolT',t); B=lambda t:L('babka',t)
intro=[N('BOOŽE, to kto mi teraz volá… Eva?'),E('Nikuška… prepáč, že ťa budím. Ja… Ja… Spravila som niečo hrozné.'),N('Čo sa stalo? Si v poriadku?'),
 E('Marek… on bol po tom víne úplne iný. Chytil ma pod krkom, Nika. Pri stole. Ja som ho odstrčila… a… a on spadol… a udrel sa o roh stola.'),
 E('Nedýcha, Nika. Ja som tam stála a čakala, že sa pohne. A on sa nepohol.'),N('Preboha, kde si teraz?'),
 E('Utiekla som. Sedím v aute. Neviem ani, kde som… niekde za mestom. Aj mňa udrel, trochu krvácam, ale to nič.'),N('Krvácaš? Odkiaľ?'),
 E('Z ruky. To nič, Niku, to nič… Počúvaj ma.'),N('Eva, musím zavolať záchranku. Aj pre neho. Možno ešte žije.'),
 E('Nežije, Nika. Ja viem, ako vyzerá mŕtvy človek. Aj ty to vieš.'),E('A keď tam príde polícia, je koniec. Ja už mám tú vec spred troch rokov. S Robom. Podmienku. Nikto mi neuverí, že som sa bránila.'),
 E('Zoberú mi Tobiho, Nika. Zoberú mi ho.')]
a1=[N('Dobre. Dobre, Eva. Pomôžem ti. Povedz mi, čo mám robiť.'),E('Ďakujem… ďakujem, Nikuška. Ja som vedela, že ty…'),E('Musíš ísť ku mne do bytu. Kým tam niekto príde.')]
a2=[N('Eva, počúvaj ma. Musíš sa prihlásiť. Zavolaj 158 a ja tam budem s tebou. Poviem, že si sa bránila. Budem pri tebe celý čas.'),E('Takže aj ty…'),
 N('Eva? Eva!'),N('Nie… Eva, nerob to. Zodvihni to…'),N('Poslala mi správu… „Prepáč. Postaraj sa o Tobiho.“'),N('Nie… Eva, nerob to. Zodvihni to…'),
 N('Dobre! Dobre. Prídem. Urobím, čo chceš. Len nerob nič hlúpe. Prosím ťa.'),E('Choď, prosím, ku mne do bytu. Kým tam niekto príde.')]
ob=[N('A kľúče máš niekde schované?'),E('V kvetináči pri dverách. Ako vždy.'),E('A Nika… tú obálku, čo som ti dala. Máš ju u babky?'),N('Hej. V taške.'),
 E('Zober ju so sebou. Prosím ťa. Nesmie ostať u babky. Nesmie ostať nikde.'),N('Čo v nej je, keď ju potrebuješ?'),E('Neskôr. Teraz nie. Sľúb mi, že ju zoberieš.')]
b1=[N('Sľubujem. Zoberiem ju.')]
b2=[N('Sľubujem. Zoberiem ju.'),T('Prepáč, Eva. Musím vedieť, do čoho idem.'),T('USB kľúč. A lístok.'),T('„Ak sa mi niečo stane, daj to niekomu mimo nášho oddelenia.“'),T('Mimo nášho oddelenia? Eva, do čoho si sa to zase…')]
b3=[N('Sľubujem. Zoberiem ju.'),T('Babkin košík s vlnou. Tam nikto hľadať nebude.'),T('Klamem jej. Prvýkrát za pätnásť rokov.')]
od=[E('Nika? Ešte si tam?'),N('Som. Obliekam sa. Ostaň na telefóne. Nepoložíš mi to, jasné?'),E('Nepoložím. Budem tu.'),B('Nikolka? Čo sa deje? Kam ideš v takom čase?')]
jobs={'s3_intro':[(intro,0,1e9)],'s3_a1x':[(a1,0,13.9),(ob,13.9,1e9)],'s3_a2x':[(a2,0,44.26),(ob,44.26,1e9)],'s3_a3x':[(a1,0,16.0),(ob,16.0,1e9)],
 's3_2_1x':[(b1,0,8.58),(od,8.58,1e9)],'s3_2_2x':[(b2,0,24.2),(od,24.2,1e9)],'s3_2_3x':[(b3,0,18.65),(od,18.65,1e9)]}
out={}
for k,parts in jobs.items():
    S=segs(A+k+'.mp3'); res=[]
    for lines,a,b in parts:
        ss=[s for s in S if s[0]>=a-0.05 and s[0]<b]
        res+=fit(ss,lines)
    out[k]=res
    print(k);[print('  %6.2f %6.2f %-7s %s'%(r['at'],r['end'],r['who'],r['text'][:60])) for r in res]
json.dump(out,open('/tmp/k3fit.json','w'),ensure_ascii=False)
