# AI Running Coach

AI Running Coach è un progetto per costruire un coach personale, locale e **CLI-first** che usa i dati degli allenamenti per proporre e adattare un piano di corsa. L'obiettivo è mantenere l'atleta al centro delle decisioni: il sistema analizza, spiega e propone, mentre l'approvazione del piano e l'eventuale inserimento degli allenamenti in Garmin Connect restano manuali.

> **Stato del progetto:** implementazione incrementale dell'MVP. Sono disponibili il package installabile, `setup` e la diagnostica dello store locale; importazione, review e pianificazione arriveranno nei ticket successivi.

## Installazione e prima configurazione

Richiede Python 3.11 o successivo. Il package non ha dipendenze runtime:

```text
python -m venv .venv
.venv\Scripts\python -m pip install .
running-coach --version
```

Su macOS e Linux usare `.venv/bin/python` e `.venv/bin/running-coach`. È disponibile un solo entry point: `running-coach`.

Senza `RUNNING_COACH_HOME`, configurazione e database vengono salvati nella directory dati dell'utente del sistema operativo. La variabile può indicare uno spazio diverso per test o uso portabile.

Il setup interattivo è disponibile soltanto quando stdin e stdout sono TTY. Per automazione e agenti usare la modalità non interattiva, che scrive un singolo documento JSON su stdout:

```text
running-coach setup --non-interactive --name Ada --available-days tuesday,thursday,sunday --preferred-long-run-day sunday --goal-type 10k --goal-date 2027-04-11 --goal-mode time --target-time 00:49:30 --goal-priority high
```

`--goal-type` accetta `general`, `5k`, `10k`, `half-marathon` e `marathon`. Ogni obiettivo richiede data, modalità `completion` oppure `time` e priorità `low`, `medium` oppure `high`; `time` richiede anche `--target-time HH:MM:SS`. Le Sessioni palestra previste sono lunedì e venerdì. Rilanciare `setup` con soli campi da correggere conserva gli altri valori: un replay identico riusa le revisioni, mentre una modifica crea una nuova revisione soltanto per la configurazione cambiata.

La diagnostica non inizializza né modifica lo store:

```text
running-coach doctor --format json
```

Gli stati dello store sono `valid`, `not_initialized` e `incompatible`.

| Codice | Significato |
| ---: | --- |
| `0` | Comando riuscito; per `doctor`, store valido |
| `2` | Input mancante/non valido oppure modalità interattiva richiesta senza TTY |
| `3` | Store non inizializzato |
| `5` | Store incompatibile o con schema non supportato |

In modalità non interattiva anche gli errori sono JSON strutturati. Progress e diagnostica non appartenenti al risultato sono riservati a stderr.

## Obiettivo

L'MVP dovrà:

- importare in sola lettura le attività di corsa da Garmin Forerunner 165;
- importare in sola lettura le attività di ciclismo da Garmin Edge 530;
- acquisire manualmente le sessioni di palestra;
- usare Whoop come unica fonte automatica per sonno e recovery;
- costruire una baseline dell'atleta e un piano orientato a un obiettivo running;
- confrontare le sedute pianificate con quelle eseguite;
- proporre revisioni settimanali e una ricalibrazione mensile;
- produrre output locali e versionati in Markdown e JSON, con provenienza dei dati, incertezza e motivazioni esplicite.

Il progetto è **running-first**: ciclismo e palestra contribuiscono alla valutazione del carico e della fatica, ma non vengono convertiti artificialmente in chilometri di corsa equivalenti.

## Principi e limiti di sicurezza

- **Garmin read-only by construction:** un gateway con allowlist e comportamento fail-closed dovrà esporre soltanto le operazioni di lettura necessarie. Il coach non potrà creare, modificare, programmare o cancellare workout su Garmin Connect.
- **Controllo umano:** ogni piano è una proposta. Le modifiche importanti richiedono conferma e nessuna bozza diventa attiva senza approvazione dell'atleta.
- **Deterministico prima del generativo:** normalizzazione, calcoli, vincoli e regole di sicurezza saranno codice verificabile. Il modello linguistico avrà un ruolo non autoritativo di interpretazione e spiegazione.
- **Dati mancanti espliciti:** il sistema non inventa valori. Completezza, qualità e confidenza vengono conservate e mostrate.
- **Privacy locale:** dati personali, segreti, audit e output restano locali per impostazione predefinita; verso un provider LLM viene inviato soltanto il contesto minimo necessario e l'uso del modello è opt-in.
- **Nessun uso clinico:** il progetto non fornisce diagnosi, riabilitazione o sostituzione di medici, fisioterapisti e allenatori.

## Architettura prevista

Il flusso logico separa nettamente acquisizione, decisioni deterministiche e contributo generativo:

```text
Garmin MCP (sola lettura) ─┐
Whoop API v2 ──────────────┼─> normalizzazione e qualità ─> storage locale
Input palestra manuale ────┘                                │
                                                            v
                                           feature e regole deterministiche
                                                            │
                                                            v
                                           proposta del coach + safety review
                                                            │
                                                            v
                                            approvazione umana e output locali
```

Le scelte architetturali complete, lo scope e i criteri di accettazione sono documentati in [AI_RUNNING_COACH_ARCHITECTURE.md](./AI_RUNNING_COACH_ARCHITECTURE.md). Il vocabolario condiviso del dominio è raccolto in [CONTEXT.md](./CONTEXT.md).

## Come è stata usata la skill `wayfinder`

`wayfinder` è una skill di pianificazione per lavori troppo grandi o incerti da affrontare in una sola sessione. Invece di trasformare subito l'idea in ticket di implementazione, crea su GitHub Issues una **mappa di decisioni** che rende visibile il percorso verso una destinazione precisa.

Nel progetto la destinazione è arrivare a una specifica implementabile dell'MVP locale, CLI-first e read-only. La [mappa Wayfinder](https://github.com/mirkosaracino98/garmin/issues/1) è la fonte aggiornata per seguire questo percorso.

La mappa funziona così:

1. definisce la **destinazione**, che delimita il risultato atteso e lo scope;
2. rappresenta ogni domanda già formulabile come un **ticket di decisione** figlio;
3. collega le dipendenze tra ticket, rendendo visibile la **frontiera**, cioè le decisioni aperte che possono essere affrontate subito;
4. conserva nella sezione **Not yet specified** la “nebbia” ancora troppo vaga per diventare un ticket;
5. quando un ticket viene risolto, registra la risposta nel ticket e aggiunge alla mappa un breve collegamento alla decisione, senza duplicarne i dettagli;
6. termina quando non resta più nulla da decidere prima di scrivere la specifica e iniziare l'implementazione.

I ticket sono classificati in base al lavoro necessario:

- `wayfinder:research` per verificare fonti, API e contratti esterni;
- `wayfinder:grilling` per chiarire scelte e trade-off insieme all'utente;
- `wayfinder:prototype` per produrre un artefatto rapido su cui raccogliere feedback;
- `wayfinder:task` per un'attività concreta che deve essere completata prima di poter decidere.

In questo repository Wayfinder ha già guidato decisioni su accesso Whoop, contratto Garmin in sola lettura, confine AGPL, baseline, modello di carico, intensità, matching piano-esecuzione, ciclismo, palestra, storage, strategia LLM e flusso CLI. Le decisioni concluse sono sintetizzate e collegate nella mappa; i ticket aperti mostrano ciò che manca per chiudere la specifica.

Wayfinder è quindi uno strumento usato **prima dell'implementazione**: evita di costruire su assunzioni non risolte e lascia una traccia consultabile delle alternative, delle motivazioni e delle conseguenze di ogni scelta.

## Contenuto attuale del repository

```text
.
├── README.md
├── AI_RUNNING_COACH_ARCHITECTURE.md   # architettura e brief operativo
├── CONTEXT.md                         # linguaggio condiviso del dominio
├── AGENTS.md                          # istruzioni per gli agenti che lavorano nel repo
├── docs/agents/                       # convenzioni per issue tracker e dominio
└── tests/fixtures/synthetic/          # payload Garmin sintetici e sanificati
```

Per orientarsi nel progetto:

1. leggere questo README per obiettivi, vincoli e stato;
2. consultare [l'architettura](./AI_RUNNING_COACH_ARCHITECTURE.md) per il disegno completo dell'MVP;
3. usare [la mappa Wayfinder](https://github.com/mirkosaracino98/garmin/issues/1) per decisioni concluse, attività aperte e avanzamento corrente;
4. consultare [il modello di dominio](./CONTEXT.md) prima di introdurre nuovi termini o schemi.

## Dipendenze di riferimento e licenze

Il progetto prevede di usare:

- [`etweisberg/garmin-connect-mcp`](https://github.com/etweisberg/garmin-connect-mcp) come processo MCP esterno e separatamente installato per l'accesso read-only a Garmin Connect;
- [`leonzzz435/garmin-ai-coach`](https://github.com/leonzzz435/garmin-ai-coach) come riferimento architetturale, senza riutilizzarne le assunzioni incompatibili con i vincoli di questo progetto.

`garmin-connect-mcp` è trattato come dipendenza AGPL-3.0 eseguita fuori processo e non distribuita insieme al coach. Qualunque futura incorporazione, modifica, fork, bundle o distribuzione richiederà una nuova verifica degli obblighi di licenza.
