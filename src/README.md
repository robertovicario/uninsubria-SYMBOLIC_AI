# Calendario degli esami: prototipo CSP

Python 3.9 o successivo, sola libreria standard. Eseguire dalla radice del repository:

```sh
python3 project/exam_scheduler/scheduler.py
python3 project/exam_scheduler/scheduler.py --impossible
python3 project/exam_scheduler/scheduler.py --algorithm mrv_fc
python3 project/exam_scheduler/scheduler.py percorso/istanza.json --max-attempts 100000
python3 -m unittest discover -s project/exam_scheduler -p 'test_*.py' -v
```

Ogni variabile rappresenta un esame, ogni valore una coppia (fascia, aula).
Capienza e disponibilità filtrano i domini iniziali. Le assegnazioni non possono
condividere nella stessa fascia aula, docenti o gruppi di studenti.
I gruppi sono identificatori espliciti: usare lo stesso identificatore per esami
con studenti condivisi. Il numero `students` serve solo al controllo di capienza.
Ogni esame occupa esattamente una fascia; le fasce sono disgiunte.
L'assenza di `available` indica disponibilità completa, una lista vuota nessuna.
Docenti e dati dell'esempio sono fittizi.

## Confronto

- `backtracking`: ordine dell'input e verifica delle assegnazioni.
- `mrv`: sceglie la variabile con meno valori compatibili con le assegnazioni.
- `mrv_fc`: MRV e forward checking sui domini delle variabili non assegnate.

Ordine dei valori e spareggi sono deterministici. Il forward checking opera
su copie dei domini per ripristinarli correttamente dopo un ramo fallito.
Ogni soluzione viene verificata anche da un controllo separato dalla ricerca.

Tentativi = valori esaminati dal ciclo di ricerca, inclusi quelli incompatibili.
Backtrack = assegnazioni compatibili annullate dopo un ramo fallito.
Potature = valori rimossi dal forward checking, anche in rami poi abbandonati.
MRV esegue controlli aggiuntivi non inclusi nei tentativi: meno tentativi non
significa necessariamente meno tempo. I millisecondi includono costruzione
dei domini e ricerca, escludendo caricamento JSON e verifica finale.

Il limite di tentativi interrompe la ricerca con esito distinto dall'impossibilità;
non è un limite temporale. L'esempio è volutamente piccolo: serve a mostrare il
funzionamento, non a dimostrare superiorità generale. Per esperimenti attendibili
serviranno più istanze, dimensioni crescenti e misure ripetute.

Il prototipo cerca la prima soluzione valida, senza ottimizzare preferenze o
distanze fra esami. `--impossible` restringe tutti gli esami alla prima fascia:
nell'esempio i conflitti rendono impossibile il calendario.
