const fs=require('fs');const D=require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel}=D;
const dlg=JSON.parse(fs.readFileSync('/tmp/dlg_new.json','utf8'));
const off=JSON.parse(fs.readFileSync('cela_hra_offsets.json','utf8'));
const names={intro:'Úvod – sprievodca',s1_blok1:'Ráno – auto, dážď',navod:'Návod pred prvým rozhodnutím',s1_navrat:'Ráno – návrat do auta',s1_zaver:'Ráno – záver v aute',s2_partA:'Stanica – časť A',s2_vetva_priznat:'Stanica – vetva Priznať',s2_vetva_vratit:'Stanica – vetva Vrátiť',s2_partB:'Stanica – časť B',s2_vecer_scena:'Večer – rozlúčka s Evou',s3_intro:'Kapitola 3 – hovor o 1:47',s3_a1x:'K3 – Pomôžem ti',s3_a2x:'K3 – Musíš sa prihlásiť',s3_a3x:'K3 – Sľúbiť a nahrávať',s3_2_1x:'K3 – Zobrať obálku',s3_2_2x:'K3 – Otvoriť obálku',s3_2_3x:'K3 – Nechať obálku u babky',k3_sluzba:'K3 – Babke: služba',k3_pravda:'K3 – Babke: pravda',k3_zaver:'K3 – Záver'};
const W={eva:'EVA',nikol:'NIKOL',nikolT:'NIKOL (v duchu)',babka:'BABKA',guide:'SPRIEVODCA',centrala:'CENTRÁLA (AĎO)',lucy:'LUCY',kollar:'KOLLÁR',disp:'CENTRÁLA (AĎO)'};
const ts=t=>{t=Math.max(0,Math.round(t));return String(Math.floor(t/60)).padStart(2,'0')+':'+String(t%60).padStart(2,'0')};
const P=(runs,o={})=>new Paragraph({children:runs,spacing:{after:80},...o});
const ch=[P([new TextRun({text:'Prípad Eva – opravený prepis',bold:true,size:36})]),
P([new TextRun({text:'Zdroj: Pripad_Eva_cela_hra_na_prepis.mp3. Časy sedia s týmto súborom (scény idú za sebou so 4 s pauzou). Text je opravený podľa nahrávok, postavy priradené správne, jedna replika na riadok.',size:20,color:'555555'})]),
P([new TextRun({text:'Čo som zmenil oproti Wordu a čo treba skontrolovať, je na konci.',size:20,color:'555555'})])];
const changed=new Set(['s3_a1x','s3_a2x','s3_a3x','s3_2_2x','s3_2_3x']);
for(const k of Object.keys(off)){
  ch.push(new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun(`${ts(off[k][0])}  ${names[k]} (${k})`)]}));
  for(const l of dlg[k]){
    const who=W[l.who]||l.who.toUpperCase();
    ch.push(P([new TextRun({text:ts(off[k][0]+(l.at||0))+'  ',color:'888888'}),new TextRun({text:who+': ',bold:true,italics:l.who==='nikolT'}),new TextRun({text:l.text,italics:l.who==='nikolT'})]));
  }
}
ch.push(new Paragraph({heading:HeadingLevel.HEADING_2,children:[new TextRun('Opravy a poznámky')]}));
const notes=[
'Word zle priradil postavy (Rečník 4–15, Eva namiesto Nikol a pod.) a zlial viac replík do jedného odseku. Všetko je rozdelené a priradené znova.',
'Opravené preklepy z prepisu: Nicol → Nikol, Trvanásť → Hliadka dvanásť, efk → Evka, tenderi → Tinderi, roch → roh, tobyho → Tobiho, u s. b → USB, Rečník „V noci veci“ → „V noci? Veď si mala voľno…“ a ďalšie.',
'Podľa prepisu som zmenil text v hre: Nikol sa pýta „Kľúče máš niekde schované?“ (predtým „Kľúče?“), „Čo v nej je, keď ju potrebuješ zrovna teraz?“, Eva vo vetve Prihlásiť hovorí „Choď, prosím, ku mne do bytu“.',
'Vetva Prihlásiť: poradie je teraz „Eva? Eva!“ → „Nie… Eva, nerob to. Zodvihni to…“ → v duchu „Poslala mi správu. Prepáč. Postaraj sa o Tobiho.“ → znova „Nie… Eva, nerob to…“ → „Dobre! Dobre. Prídem…“.',
'Vetvy Otvoriť obálku a Nechať u babky začínajú „Sľubujem. Zoberiem ju.“ (predtým „Dobre.“ a „Hej. Mám ju.“).',
'POZOR – vetva Sľúbiť a nahrávať (s3_a3x): podľa prepisu v nej Nikol hovorí to isté ako vo vetve Pomôžem ti. Myšlienky o nahrávaní („Prepáč, Eva. Ale nemôžem riskovať…“, „Nahrávanie beží…“) v nahrávke nie sú. Ak tam majú byť, treba ich do nahrávky doplniť.',
'Word nezachytil tieto repliky, nechal som ich podľa scenára – over, či v nahrávke sú: začiatok K3 („BOOŽE, to kto mi teraz volá… Eva?“, „Nevydaril sa ti ten stoosemdesiatcentimetrový?“), „Nie. Nie, nie, nie. Toto sa nedeje.“, „Preboha“, v návode „Polož prst na obrazovku a podrž ho…“, na stanici „Veď je piatok.“, „Stále vypnutý.“, „Neotváraj, povedala…“, „Neskôr. Teraz je tu Marek.“, „Babka. Samozrejme.“ a v závere „Nikuška?“ – „Hm?“.'];
for(const n of notes) ch.push(P([new TextRun('• '+n)]));
const doc=new Document({styles:{default:{document:{run:{font:'Calibri',size:22}},heading2:{run:{font:'Calibri',size:26,bold:true,color:'1F3864'},paragraph:{spacing:{before:240,after:100},keepNext:true}}}},sections:[{children:ch}]});
Packer.toBuffer(doc).then(b=>fs.writeFileSync('/mnt/user-data/outputs/Pripad_Eva_prepis_opraveny.docx',b));
