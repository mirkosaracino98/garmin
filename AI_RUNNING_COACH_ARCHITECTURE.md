# AI Running Coach personale — architettura e brief operativo

> Documento di ingresso per `/wayfinder` e per le successive fasi di specifica e implementazione.
>
> Stato: direzione del prodotto definita; alcune decisioni tecniche sono intenzionalmente lasciate come “fog” da risolvere.

## 1. Destinazione del progetto

Costruire un AI Running Coach personale, locale e **closed loop**, che:

1. legge in sola lettura gli allenamenti di corsa registrati con Garmin Forerunner 165;
2. legge in sola lettura le attività di ciclismo registrate con Garmin Edge 530;
3. riceve manualmente le sessioni di palestra non tracciate;
4. usa dati di riposo, sonno e recovery esclusivamente da Whoop, mai da Garmin;
5. stima il livello corrente dell’atleta e costruisce un piano orientato a un obiettivo di corsa;
6. confronta piano e allenamenti realmente svolti;
7. adatta il piano ogni settimana e ricalibra il blocco ogni mese;
8. produce piani e spiegazioni leggibili, che l’utente inserirà manualmente in Garmin Connect se desiderato.

Il prodotto non deve creare, programmare, modificare o cancellare workout su Garmin Connect.

### Risultato atteso

Un’applicazione CLI-first, utilizzabile da Codex o Claude Code, capace di generare:

- profilo e baseline iniziale dell’atleta;
- valutazione degli allenamenti dell’ultima settimana;
- piano di corsa dei successivi 7 giorni;
- vista del blocco di 4 settimane e del macro-obiettivo;
- motivazione sintetica di ogni adattamento;
- alert conservativi su incoerenze, sovraccarico o dati mancanti;
- file Markdown e JSON versionati localmente.

## 2. Decisioni già fissate

Queste scelte costituiscono vincoli, non alternative da riesaminare durante la prima fase.

### Data Layer Garmin

Usare **[`etweisberg/garmin-connect-mcp`](https://github.com/etweisberg/garmin-connect-mcp)** come server MCP e adapter per Garmin Connect.

Responsabilità nel progetto:

- autenticazione e sessione Garmin;
- lettura delle attività e dei relativi dettagli;
- lettura di statistiche sportive utili;
- esposizione dei dati grezzi al layer di normalizzazione.

Il repository espone anche tool per creare, programmare o cancellare workout. **Tali tool devono essere esclusi dalla allowlist dell’applicazione e non devono essere richiamabili dagli agenti del coach.** Il progetto deve aggiungere un gateway read-only, test contrattuali e logging delle chiamate MCP.

### Coach Architecture

Usare **[`leonzzz435/garmin-ai-coach`](https://github.com/leonzzz435/garmin-ai-coach)** come riferimento per l’architettura del coach.

Riutilizzare o adattare:

- pipeline di summarizer ed expert agent;
- orchestrazione multi-agent con LangGraph;
- separazione fra analisi, piano stagionale/blocco e piano dettagliato;
- output strutturati intermedi;
- human-in-the-loop per informazioni mancanti o decisioni importanti;
- test dei componenti di analisi e pianificazione.

Non copiare senza modifiche:

- il data extractor Garmin nativo del repository;
- i moduli che usano HRV, sonno, resting HR o readiness provenienti da Garmin;
- assunzioni multisport che compromettono la priorità dell’obiettivo running;
- qualunque meccanismo di pubblicazione automatica del piano.

Il nuovo progetto deve integrare il MCP scelto come Data Layer e trattare Whoop come unica fonte ammessa per recovery e sonno.

### Nota licenze

Al momento della definizione del progetto, `garmin-connect-mcp` dichiara licenza AGPL-3.0 e `garmin-ai-coach` licenza MIT. Prima di distribuire il software o incorporare codice del Data Layer, aprire una decisione specifica su confini di processo, obblighi di distribuzione e attribuzioni. Per uso personale locale, documentare comunque dipendenze e licenze.

## 3. Scope

### Incluso

- obiettivi running: 5 km, 10 km, mezza maratona, maratona o obiettivo generale;
- data target, distanza, tempo desiderato e priorità;
- storico Garmin di corsa e ciclismo;
- sessioni palestra inserite manualmente;
- import di sonno/recovery da Whoop attraverso un adapter separato;
- baseline iniziale, periodizzazione, piano settimanale e blocco mensile;
- adattamento basato su esecuzione, carico, trend di performance, cross-training e disponibilità;
- output locale in Markdown e JSON;
- spiegazioni e provenance dei dati usati per ogni decisione;
- gestione esplicita dei dati mancanti;
- conferma umana prima di cambiamenti importanti al blocco.

### Escluso

- scrittura, scheduling o cancellazione automatica di workout su Garmin Connect;
- sincronizzazione automatica di workout verso Forerunner 165 o Edge 530;
- metriche Garmin relative a sonno, riposo o recovery;
- inferenza automatica degli allenamenti in palestra non registrati;
- coaching clinico, diagnosi medica o riabilitazione;
- sostituzione del giudizio di medico, fisioterapista o allenatore;
- piano nutrizionale completo;
- social, classifiche o coaching multiutente nell’MVP;
- app mobile e interfaccia web nell’MVP.

## 4. Principi di progettazione

1. **Running first:** il ciclismo e la palestra supportano o condizionano il piano, ma l’obiettivo primario resta la corsa.
2. **Read-only by construction:** la sicurezza non dipende dal prompt; il gateway MCP rende disponibili solo operazioni di lettura.
3. **Source-aware:** ogni metrica conserva fonte, timestamp, unità e qualità.
4. **No fabricated data:** ciò che non è tracciato viene marcato come mancante o richiesto all’utente.
5. **Recovery isolation:** Garmin non è mai fonte di recovery; Whoop è l’unica fonte automatica prevista per questo dominio.
6. **Deterministic before generative:** calcoli, normalizzazione, regole di sicurezza e vincoli di piano sono codice testabile; il modello interpreta e spiega.
7. **Human control:** il piano è una proposta locale; l’utente ne mantiene approvazione e inserimento nei propri strumenti.
8. **Conservative adaptation:** una singola giornata anomala non deve riscrivere l’intero piano.
9. **Auditability:** input, trasformazioni, decisioni e versioni del piano sono ricostruibili.
10. **Privacy by default:** segreti e dati personali restano locali salvo chiamate esplicitamente necessarie al provider LLM configurato.

## 5. Architettura logica

```text
Garmin Forerunner 165 ─┐
  running              │
                       ├─> Garmin Connect
Garmin Edge 530 ───────┘        │
  cycling                       │ read-only
                                v
                   etweisberg/garmin-connect-mcp
                                │
                                v
                         MCP Read Gateway
                         allowlist + audit
                                │
Whoop ─> Whoop Adapter ─────────┼──> Normalization & Validation
 sleep/recovery only            │          │
                                │          v
Manual gym entry ───────────────┘    Local Athlete Store
                                           │
                                           v
                                Summarizers / Feature Engine
                                           │
                         ┌─────────────────┼─────────────────┐
                         v                 v                 v
                    Load Expert      Running Expert    Recovery Expert
                         │                 │             (Whoop only)
                         └─────────────────┼─────────────────┘
                                           v
                                  Coach Orchestrator
                                           │
                              ┌────────────┴────────────┐
                              v                         v
                    Plan Generator              Adaptation Engine
                              │                         │
                              └────────────┬────────────┘
                                           v
                                Markdown + JSON output
                                manual entry by user
```

### Confini essenziali

- Il Garmin MCP è un’integrazione esterna e non il dominio del coach.
- Il MCP Read Gateway espone al resto del sistema solo metodi approvati.
- Garmin e Whoop confluiscono nel modello normalizzato, ma le fonti non vengono confuse.
- La logica deterministica calcola feature e applica vincoli; gli agenti non interrogano liberamente le fonti.
- Il planner non possiede alcuna porta di output verso Garmin Connect.

## 6. Componenti

### 6.1 Garmin MCP Adapter

Wrapper del server `etweisberg/garmin-connect-mcp`.

Responsabilità:

- controllo della sessione;
- acquisizione incrementale delle attività;
- dettaglio di attività, lap e serie quando disponibile;
- retry limitati, timeout e messaggi di errore comprensibili;
- salvataggio del payload grezzo con timestamp di acquisizione;
- nessun accesso ai tool Garmin esclusi.

Allowlist minima da finalizzare dopo un inventario della versione installata:

- session check;
- elenco/calendario delle attività;
- dettaglio attività;
- statistiche fitness sportive;
- VO2max, record personali e configurazione delle zone, se disponibili e utili.

Denylist obbligatoria:

- `create-workout`;
- `schedule-workout`;
- `delete-workout`;
- qualsiasi futuro tool mutativo;
- `get-sleep`, `get-sleep-stats`, `get-body-battery`, `get-hrv`, `get-training-readiness`;
- altre metriche Garmin classificate come recovery, readiness, riposo o sonno.

La policy deve essere **deny-by-default**: l’arrivo di un nuovo tool MCP non lo rende automaticamente disponibile.

### 6.2 Whoop Adapter

Un’unica interfaccia di dominio, indipendente dal meccanismo concreto di acquisizione:

```text
get_recovery_window(start_date, end_date) -> RecoveryObservation[]
```

Possibili implementazioni da decidere durante Wayfinder:

- API Whoop ufficiale;
- import CSV;
- inserimento manuale giornaliero.

Per l’MVP è accettabile un import manuale/CSV, purché il contratto resti sostituibile. Nessun fallback su Garmin in caso di assenza del dato Whoop.

### 6.3 Manual Gym Input

Comando guidato per registrare almeno:

- data;
- durata;
- tipo: forza generale, lower body, upper body, full body, core/mobility;
- RPE sessione 1–10;
- carico sulle gambe: basso, medio, alto;
- DOMS/dolore muscolare segnalato: nessuno, lieve, significativo;
- note opzionali;
- prossima sessione prevista, se nota.

Il sistema non inventa volume, serie, ripetizioni o tonnellaggio. L’inserimento manuale può essere modificato e mantiene traccia della revisione.

### 6.4 Normalization & Validation

Converte i dati in contratti interni stabili:

- unità canoniche SI e rappresentazioni di passo esplicite;
- timezone locale Europe/Rome con timestamp originali conservati;
- sport normalizzato (`running`, `cycling`, `strength_manual`, `other`);
- deduplicazione tramite identificatore fonte;
- flag di completezza e qualità;
- provenienza per ogni campo;
- schema versionato e validato.

### 6.5 Local Athlete Store

Per MVP: database SQLite più artefatti JSON/Markdown.

Entità minime:

- `AthleteProfile`;
- `Goal`;
- `AvailabilityConstraint`;
- `Activity`;
- `ActivitySplit`;
- `WhoopRecoveryObservation`;
- `ManualStrengthSession`;
- `FitnessSnapshot`;
- `TrainingPlan`;
- `PlannedSession`;
- `PlanRevision`;
- `CoachDecision`;
- `DataImportRun`.

### 6.6 Feature Engine

Calcoli deterministici e testabili:

- volume e durata running per 7, 28 e 42 giorni;
- frequenza settimanale e continuità;
- distribuzione intensità per zone disponibili;
- carico interno da frequenza cardiaca e/o session RPE quando disponibile;
- carico esterno da distanza, dislivello, passo e potenza se disponibile;
- monotonia e strain con soglie configurabili;
- trend di passo a FC comparabile;
- prestazione su intervalli, tempo run e lunghi;
- aderenza al piano per durata, distanza, intensità e intento;
- carico ciclismo separato e conversione prudente in stress sistemico;
- impatto palestra sulle gambe, senza fingere equivalenza con chilometri di corsa;
- trend Whoop su finestra, senza usare un singolo score come verdetto assoluto.

ACWR o metriche analoghe possono essere mostrate come segnali descrittivi, non come soglie mediche o unico motore decisionale.

## 7. Modello dati minimo

Ogni osservazione deve includere almeno:

```json
{
  "source": "garmin|whoop|manual|derived",
  "source_id": "string|null",
  "observed_at": "ISO-8601",
  "imported_at": "ISO-8601",
  "schema_version": "string",
  "quality": "complete|partial|suspect|missing",
  "value": {},
  "provenance": {}
}
```

### Profilo atleta

- età o fascia d’età, se fornita;
- sesso, solo se fornito e necessario ai modelli selezionati;
- esperienza di corsa;
- storico infortuni dichiarato;
- giorni e tempo disponibili;
- preferenze e vincoli;
- numero massimo desiderato di sedute running;
- disponibilità ciclismo e palestra;
- zone FC/potenza note e metodo con cui sono state determinate.

### Obiettivo

- distanza;
- evento e data;
- tempo target o obiettivo di completamento;
- priorità A/B/C;
- percorso noto, dislivello e superficie, se disponibili;
- motivazione e tolleranza al rischio dichiarate;
- stato: proposto, attivo, raggiunto, rinviato o annullato.

## 8. Metriche incluse ed escluse

### Garmin — incluse

Solo se effettivamente presenti nei dati dell’attività o nel profilo sportivo:

- tipo sport, data, durata, distanza;
- passo/velocità medi e per lap;
- frequenza cardiaca media, massima e distribuzione per zone;
- cadenza;
- dislivello;
- potenza running o cycling;
- lap, intervalli e struttura dell’attività registrata;
- Training Effect aerobico/anaerobico come segnale secondario, se disponibile;
- VO2max sport-specifico come trend secondario;
- personal record e race prediction come contesto, non verità assolute;
- temperatura o condizioni registrate, con bassa affidabilità quando provengono dal dispositivo;
- metriche cycling equivalenti registrate dall’Edge 530.

### Garmin — escluse senza eccezioni

- sonno, sleep score, durata e fasi;
- HRV e HRV status Garmin;
- Body Battery;
- Training Readiness;
- recovery time;
- stress giornaliero;
- resting heart rate usata come metrica di recovery;
- respiration e Pulse Ox notturni;
- readiness o recovery composite derivati da una delle metriche sopra;
- qualunque metrica di riposo/sonno/recovery introdotta in futuro dal MCP.

Anche se questi campi compaiono nei payload Garmin, devono essere scartati in ingestione e non salvati nel modello normalizzato.

### Whoop — incluse

Da confermare in base al metodo di accesso scelto:

- recovery score;
- sleep performance/durata;
- HRV;
- resting heart rate;
- respiratory rate;
- strain;
- trend e baseline Whoop;
- timestamp, completezza e affidabilità del dato.

Le metriche Whoop influenzano prudenzialmente volume e intensità a breve termine; non devono cambiare da sole l’obiettivo di lungo periodo.

### Palestra — incluse manualmente

- presenza della sessione;
- durata;
- RPE;
- focus muscolare;
- carico stimato sulle gambe;
- DOMS dichiarato;
- note e pianificazione futura.

### Non osservabile

Se una sessione di palestra non viene inserita, il coach deve dichiarare: “palestra non registrata / dato sconosciuto”. Non deve concludere che non sia avvenuta.

## 9. Agenti e skill suggeriti

L’architettura prende ispirazione dagli expert agent e dal master orchestrator di `garmin-ai-coach`, ma impone input strutturati e responsabilità strette.

### Agenti runtime del coach

#### Data Quality Agent

- individua buchi, duplicati e anomalie;
- non corregge silenziosamente;
- produce una scheda di affidabilità per la settimana.

#### Athlete Baseline Agent

- stima livello ed esperienza dai trend, non da una sola gara;
- separa capacità osservata e assunzioni;
- propone zone o ritmi solo con livello di confidenza esplicito.

#### Running Performance Expert

- valuta endurance, velocità, soglia, lunghi e consistenza;
- confronta intento della seduta ed esecuzione;
- distingue mancata aderenza da segnali di affaticamento o vincoli esterni.

#### Cross-Training Load Expert

- valuta il ciclismo come lavoro aerobico e stress aggiuntivo;
- valuta la palestra manuale come carico neuromuscolare;
- non converte automaticamente bici o palestra in chilometri equivalenti.

#### Recovery Expert — Whoop only

- riceve esclusivamente osservazioni normalizzate Whoop e note manuali;
- non ha accesso al Garmin adapter;
- produce un’indicazione graduata con confidenza e dati mancanti.

#### Plan Designer

- costruisce macro-fasi, blocco di 4 settimane e settimana dettagliata;
- applica disponibilità, preferenze e vincoli del profilo;
- assegna a ogni sessione intento, volume, intensità, alternative e criteri di completamento.

#### Adaptation Agent

- confronta piano, esecuzione, risposta e vincoli futuri;
- propone modifiche limitate e motivazioni strutturate;
- scala le decisioni ad alto impatto alla conferma umana.

#### Safety & Consistency Reviewer

- verifica aumenti di carico, conflitti fra sedute dure, dati insufficienti e linguaggio medico;
- può bloccare la pubblicazione locale del nuovo piano finché un conflitto non è risolto;
- non diagnostica.

#### Master Coach Orchestrator

- orchestra i passaggi in LangGraph;
- sintetizza senza sovrascrivere i segnali contrari;
- produce output finale, assumptions, confidence e changelog;
- non ha tool Garmin mutativi.

### Skill di sviluppo suggerite

Percorso consigliato per Matt Pocock skills:

1. `/wayfinder` per risolvere le decisioni ancora incerte elencate nella sezione 16;
2. `/research` per API Whoop, contratti reali del Garmin MCP e modelli di carico;
3. `/domain-modeling` per stabilire entità, invarianti e confini;
4. `/to-spec` quando la mappa Wayfinder non contiene più decisioni bloccanti;
5. `/to-tickets` per dividere la specifica in unità implementabili;
6. `/implement` o flusso TDD equivalente per l’esecuzione;
7. `/code-review` e test di integrazione prima del rilascio dell’MVP.

Il prompt iniziale a `/wayfinder` può essere:

> Destination: costruire l’MVP locale e read-only descritto in `AI_RUNNING_COACH_ARCHITECTURE.md`, capace di analizzare running Garmin, ciclismo Garmin, recovery Whoop e palestra manuale, generando un piano running adattivo senza mai scrivere su Garmin Connect. Tratta le decisioni fissate nelle sezioni 1–3 come vincoli. Crea ticket di decisione soltanto per la fog elencata nella sezione 16 e per nuova fog realmente bloccante.

## 10. Flussi dati

### 10.1 Prima configurazione

1. L’utente configura credenziali/sessione Garmin fuori dai file versionati.
2. Il sistema valida la connessione MCP e l’allowlist.
3. L’utente sceglie il metodo Whoop disponibile.
4. L’utente completa profilo, disponibilità, storico rilevante e obiettivo.
5. Il sistema importa una finestra storica configurabile, inizialmente 8–12 settimane.
6. Data Quality Agent segnala lacune e chiede solo dati indispensabili.
7. Feature Engine costruisce la baseline.
8. Gli expert agent producono valutazioni strutturate.
9. Plan Designer propone blocco e prima settimana.
10. Safety Reviewer valida; l’utente approva localmente.

### 10.2 Aggiornamento settimanale

1. Import incrementale delle nuove attività Garmin.
2. Import delle osservazioni Whoop per lo stesso periodo.
3. Richiesta delle sessioni palestra non ancora inserite.
4. Deduplicazione, validazione e feature calculation.
5. Matching fra sessioni pianificate e attività eseguite.
6. Review di aderenza, carico e risposta.
7. Proposta della settimana successiva.
8. Safety review e controllo dei vincoli di calendario.
9. Generazione di `weekly_review.md`, `next_week_plan.md` e JSON associati.
10. L’utente inserisce manualmente i workout desiderati in Garmin Connect.

### 10.3 Revisione mensile

1. Aggregazione delle ultime 4 settimane e confronto con baseline/blocco precedente.
2. Valutazione di progressione, consistenza, tolleranza al carico e specificità.
3. Verifica della traiettoria verso l’obiettivo.
4. Aggiornamento delle priorità del blocco successivo.
5. Eventuale revisione prudente di ritmi/zone, con confidenza esplicita.
6. Aggiornamento del piano di 4 settimane e changelog.
7. Conferma umana per cambi di fase, target o volume rilevanti.

## 11. Logica di adattamento

### Regole settimanali

Il sistema considera insieme:

- percentuale e qualità di completamento delle sedute;
- volume e intensità effettivi rispetto al piano;
- tendenza di performance su sedute comparabili;
- carico running recente;
- carico cycling e sua collocazione;
- palestra lower-body e DOMS dichiarato;
- recovery Whoop e sua tendenza;
- dolore, malattia, viaggio, tempo disponibile e feedback manuale;
- qualità/completeness dei dati.

Esempi di comportamento:

- alta aderenza, performance stabile e recovery coerente: progressione prevista o minima;
- seduta chiave mancata per agenda: ripianificare solo se non crea due giorni duri consecutivi;
- carico bici elevato: ridurre o spostare il lavoro aerobico running, preservando quando sensato la specificità;
- palestra gambe ad alto carico: evitare qualità running ravvicinata e registrare l’incertezza;
- recovery Whoop negativa per un solo giorno: offrire un’alternativa facile, senza riscrivere il blocco;
- trend Whoop negativo più feedback soggettivo e calo di prestazione: settimana di assorbimento o riduzione;
- dati insufficienti: mantenere o semplificare, mai aumentare aggressivamente.

### Gerarchia degli adattamenti

Applicare, nell’ordine:

1. proteggere sicurezza e vincoli espliciti;
2. preservare recupero tra sedute impegnative;
3. mantenere l’intento della settimana;
4. modificare collocazione delle sedute;
5. modificare durata/volume;
6. modificare intensità;
7. sostituire il tipo di seduta;
8. cambiare fase o obiettivo solo con revisione mensile o conferma umana.

### Limiti configurabili

Le percentuali non devono essere hard-coded come verità universali. Il dominio deve supportare policy configurabili e versionate per:

- massimo aumento settimanale di volume;
- numero di sedute intense;
- distanza minima tra sedute impegnative;
- durata massima del lungo;
- settimana di scarico;
- sostituzioni bici/corsa;
- soglie di escalation umana.

Ogni revisione del piano salva policy version, motivazioni, evidenze e differenze rispetto alla versione precedente.

## 12. Gestione del cross-training

### Ciclismo

Il ciclismo registrato dall’Edge 530 è trattato in due dimensioni distinte:

- **beneficio aerobico:** può supportare volume aerobico con minor impatto meccanico;
- **fatica sistemica/locale:** una sessione lunga o intensa può compromettere una seduta running successiva.

Principi:

- mantenere metriche e carico separati per sport;
- usare potenza, FC, durata e intensità quando presenti;
- non equiparare automaticamente minuti bici e minuti corsa;
- non sostituire sedute specifiche di gara senza motivazione;
- permettere sostituzioni esplicite, ad esempio easy run → endurance ride, solo quando compatibili con la fase;
- considerare eventi cycling come vincoli di calendario se dichiarati.

### Palestra

La palestra è un input manuale con incertezza esplicita.

Principi:

- una sessione lower-body pesante influenza la collocazione di ripetute, salite e lungo;
- upper-body e core hanno impatto inferiore, salvo RPE/durata elevati;
- DOMS significativo provoca un alert e una proposta conservativa;
- il coach può suggerire dove collocare la palestra, ma non genera nell’MVP una scheda di forza dettagliata;
- assenza di inserimento non equivale ad assenza di palestra.

## 13. Output

### File utente

```text
data/
├── profile/
│   ├── athlete_profile.yaml
│   └── active_goal.yaml
├── plans/
│   ├── season_plan.md
│   ├── current_block.md
│   ├── next_week_plan.md
│   └── history/
├── reviews/
│   ├── weekly_review.md
│   └── monthly_review.md
├── manual/
│   └── strength_sessions.yaml
└── exports/
    ├── coach_snapshot.json
    └── plan.json
```

### Contenuto minimo del piano settimanale

Per ogni giorno:

- stato: workout, riposo, opzionale o cross-training;
- obiettivo della sessione;
- riscaldamento;
- parte centrale;
- defaticamento;
- intensità espressa con gerarchia chiara: RPE + zona FC e, quando affidabile, passo/potenza;
- durata o distanza;
- alternativa breve e alternativa conservativa;
- segnali per interrompere o ridurre;
- relazione con l’obiettivo e con le altre sedute.

Il file deve terminare con:

- assunzioni;
- dati mancanti;
- confidence;
- modifiche rispetto al piano precedente;
- istruzione esplicita: “Inserimento su Garmin Connect a cura dell’utente”.

## 14. Struttura suggerita del repository

```text
ai-running-coach/
├── README.md
├── LICENSES.md
├── pyproject.toml
├── .env.example
├── config/
│   ├── coach.example.yaml
│   ├── policies.example.yaml
│   └── schemas/
├── docs/
│   ├── architecture.md
│   ├── data-contracts.md
│   ├── privacy.md
│   ├── safety.md
│   ├── decisions/
│   └── wayfinder/
│       └── destination.md
├── src/ai_running_coach/
│   ├── cli/
│   ├── config/
│   ├── domain/
│   │   ├── athlete.py
│   │   ├── activity.py
│   │   ├── recovery.py
│   │   ├── plan.py
│   │   └── decisions.py
│   ├── integrations/
│   │   ├── garmin_mcp/
│   │   │   ├── client.py
│   │   │   ├── readonly_gateway.py
│   │   │   ├── allowlist.py
│   │   │   └── mapper.py
│   │   └── whoop/
│   │       ├── port.py
│   │       ├── csv_adapter.py
│   │       └── api_adapter.py
│   ├── ingestion/
│   ├── storage/
│   ├── features/
│   ├── matching/
│   ├── agents/
│   │   ├── data_quality.py
│   │   ├── baseline.py
│   │   ├── running_expert.py
│   │   ├── cross_training_expert.py
│   │   ├── whoop_recovery_expert.py
│   │   ├── plan_designer.py
│   │   ├── adaptation.py
│   │   ├── safety_reviewer.py
│   │   └── orchestrator.py
│   ├── workflows/
│   ├── policies/
│   ├── rendering/
│   └── observability/
├── prompts/
│   ├── versioned/
│   └── fixtures/
├── data/                       # ignorata da Git salvo esempi sintetici
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── golden/
│   └── fixtures/synthetic/
└── scripts/
```

## 15. Vincoli non funzionali e sicurezza

### Sicurezza operativa

- gateway MCP deny-by-default;
- test che fallisce se un tool mutativo entra nell’allowlist;
- agenti senza accesso diretto al processo MCP;
- nessun endpoint o modulo `publish_to_garmin`;
- log della chiamata con nome tool, orario, esito e hash degli input, senza segreti;
- segreti esclusi da repository, prompt e output;
- sessioni e cookie protetti con permessi locali appropriati;
- fixture di test sintetiche, mai dati personali reali.

### Privacy

- storage locale predefinito;
- retention configurabile per payload grezzi;
- possibilità di rigenerare le feature eliminando i raw data;
- inviare al provider LLM il minimo contesto necessario;
- documentare chiaramente se LangSmith o tracing esterno sono attivati;
- tracing esterno disattivato di default;
- comando di export e cancellazione selettiva dei dati locali.

### Affidabilità

- operazioni di import idempotenti;
- schema versionato e migrazioni;
- output riproducibile per feature deterministiche;
- timeout e retry limitati;
- modalità degradata quando Whoop o Garmin non sono disponibili;
- nessuna progressione aggressiva in presenza di dati parziali;
- snapshot del piano precedente prima di ogni revisione.

### Osservabilità

- import report;
- data quality report;
- agent input/output schema validation;
- costo/token usage opzionale;
- decision log leggibile;
- correlazione tra piano, revisione ed evidenze.

## 16. Wayfinder: fog da risolvere

Creare ticket di **decisione**, non ticket di implementazione, per i punti seguenti.

1. **Whoop access path:** API ufficiale, CSV o inserimento manuale per MVP; autenticazione, limiti e campi realmente disponibili.
2. **Garmin tool contract:** elenco esatto dei tool read-only della versione fissata del MCP e mapping dei payload reali per running/cycling.
3. **Runtime integration:** eseguire il MCP come processo esterno/versionato oppure incorporarne parti, considerando manutenzione e AGPL.
4. **Baseline window:** finestra minima necessaria e comportamento per un nuovo atleta con storico insufficiente.
5. **Load model:** combinazione iniziale di durata, FC, RPE, potenza e sport; policy quando alcuni campi mancano.
6. **Plan intensity language:** priorità fra RPE, FC, passo e potenza nei diversi tipi di seduta.
7. **Workout matching:** regole per associare attività svolte a sedute previste, incluse sostituzioni e allenamenti spostati.
8. **Adaptation thresholds:** quali modifiche possono essere automatiche localmente e quali richiedono conferma.
9. **Cycling contribution:** modello prudente per beneficio aerobico e fatica, distinto per endurance, interval e long ride.
10. **Gym input burden:** set minimo di campi che l’utente compilerà con costanza.
11. **Storage/retention:** durata di conservazione dei payload grezzi e procedura di cancellazione.
12. **Model/provider strategy:** provider, structured output, cost ceiling, fallback e modalità senza LLM per i calcoli.
13. **Evaluation:** dataset sintetico/golden cases e criteri misurabili per giudicare qualità e sicurezza del piano.
14. **License boundary:** conseguenze concrete dell’uso del server AGPL e modalità corretta di distribuzione.

La mappa è completa quando ogni punto bloccante ha una decisione registrata, trade-off espliciti e conseguenze sulla futura specifica.

## 17. MVP

### MVP obbligatorio

- configurazione locale e CLI;
- autenticazione Garmin MCP già eseguita dall’utente;
- gateway read-only con allowlist e denylist testate;
- import di 8–12 settimane di corsa e ciclismo;
- import Whoop tramite un solo adapter scelto;
- inserimento manuale palestra;
- profilo e un obiettivo running attivo;
- normalizzazione, deduplicazione e data-quality report;
- feature running/cycling/strength essenziali;
- baseline con confidenza;
- generazione blocco di 4 settimane e piano di 7 giorni;
- review settimanale e revisione mensile;
- Safety Reviewer e conferma umana;
- output Markdown + JSON;
- cronologia delle revisioni;
- nessuna scrittura Garmin, verificata da test.

### Non necessario per MVP

- dashboard web;
- app mobile;
- upload automatico del workout;
- coaching palestra dettagliato;
- molteplici obiettivi simultanei;
- notifiche push;
- previsioni gara avanzate;
- integrazione calendario;
- deployment cloud;
- fine-tuning di modelli.

### Criteri di accettazione MVP

1. Dato uno storico sintetico e un obiettivo valido, il sistema genera un piano settimanale completo e schema-valid.
2. Le attività running del Forerunner 165 e cycling dell’Edge 530 restano distinguibili dall’ingestione all’output.
3. Nessuna metrica Garmin esclusa è presente nel modello normalizzato o nei prompt degli agenti.
4. In assenza di Whoop, il piano dichiara il dato mancante e usa una policy conservativa senza fallback Garmin.
5. Una sessione palestra lower-body ad alto carico influenza il calendario senza essere trasformata in chilometri equivalenti.
6. Ogni adattamento indica evidenze, regola/policy, confidence e differenza dal piano precedente.
7. Qualunque tentativo di invocare un tool Garmin non allowlisted fallisce prima di raggiungere il MCP.
8. La suite contiene un test esplicito che prova l’impossibilità di creare, programmare o cancellare workout.
9. L’output ricorda che l’inserimento su Garmin Connect è manuale.
10. Il sistema non formula diagnosi e segnala quando serve un professionista.

## 18. Strategia di test

### Unit test

- conversione unità e timezone;
- calcoli di volume/carico;
- deduplicazione;
- policy di adattamento;
- classificazione impatto palestra;
- filtri delle metriche Garmin escluse.

### Contract test

- payload MCP Garmin → schema interno;
- payload/import Whoop → schema interno;
- structured output di ogni agente;
- allowlist/denylist MCP;
- rilevamento automatico di nuovi tool non classificati.

### Integration test

- import incrementale idempotente;
- pipeline baseline → plan;
- weekly review → plan revision;
- modalità Garmin non disponibile;
- modalità Whoop non disponibile;
- dati parziali e attività duplicate.

### Golden scenarios sintetici

- atleta consistente e pronto a progredire;
- settimana con bici molto intensa;
- palestra gambe il giorno prima delle ripetute;
- calo di recovery Whoop isolato;
- trend negativo multi-segnale;
- gara avvicinata con storico insufficiente;
- seduta chiave spostata o sostituita;
- attività Garmin priva di FC o lap;
- payload contenente metriche Garmin vietate;
- prompt injection o testo anomalo nelle note attività/manuali.

## 19. Definition of Done del progetto iniziale

Il progetto iniziale è pronto per l’uso personale quando:

- tutte le decisioni Wayfinder bloccanti sono risolte;
- specifica e contratti dati sono versionati;
- l’MVP soddisfa tutti i criteri di accettazione;
- l’utente può eseguire setup, import, review e plan da CLI seguendo il README;
- i fallimenti di Garmin, Whoop e provider LLM producono messaggi e fallback sicuri;
- privacy, segreti e retention sono documentati;
- licenze e attribuzioni sono documentate;
- test unit, contract, integration e golden passano;
- una verifica finale conferma che non esiste alcun percorso di scrittura verso Garmin Connect.

## 20. Riferimenti primari

- Data Layer: [etweisberg/garmin-connect-mcp](https://github.com/etweisberg/garmin-connect-mcp)
- Coach Architecture: [leonzzz435/garmin-ai-coach](https://github.com/leonzzz435/garmin-ai-coach)
- Planning workflow: [Matt Pocock — wayfinder](https://github.com/mattpocock/skills/blob/main/docs/engineering/wayfinder.md)

---

Questo documento descrive un sistema di supporto all’allenamento e non uno strumento medico. Dolore, sintomi, infortunio o dubbi clinici devono interrompere l’automazione e richiedere valutazione professionale.
