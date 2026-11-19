# Prípad Eva – zdrojáky

- `v2_template.html` – celá hra (HTML/CSS/JS, SCRIPT, DLG titulky, SPK mapa guľôčky, JUMPS výber scén). Miesto `/*AUDIO*/` sa nahradí obsahom `audio_engine.js`.
- `audio_engine.js` – zvukový engine (scény none/car/office/evening/night, ducking, slučky).
- Build: `python3 -c "s=open('v2_template.html').read();open('../pripad-eva/index.html','w').write(s.replace('/*AUDIO*/',open('audio_engine.js').read()))"`
- Zvuky: `../pripad-eva/a/*.mp3` (repliky, -18.5 LUFS), `../pripad-eva/s/*` (SFX, hudba, menu.jpg).
- `tools/` – Python skripty na mix, telefónny efekt (phone_split.py), vnútorný hlas, dorovnanie titulkov (subfit.py, fitk3.py), alib.py = knižnica (LUFS, filtre, kompresor, reverb).
