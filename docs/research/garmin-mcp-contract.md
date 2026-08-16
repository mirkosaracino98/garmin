# Contratto read-only del Garmin MCP

## Decisione

Per l'MVP fissare `@etweisberg/garmin-connect-mcp` alla versione **0.1.23** e alla revisione sorgente **`87d0ea059fb67f1ce65ac05100df74c3c3777c84`** (commit `release: v0.1.23`, 2026-07-12). Il gateway non deve inoltrare tool MCP per nome: deve esporre operazioni di dominio tipizzate e tradurle verso una piccola allowlist chiusa. La versione del pacchetto e le dipendenze sono dichiarate nel [`package.json` della revisione](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/package.json#L1-L38); il lock risolve [MCP SDK 1.28.0](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/package-lock.json#L707-L713), [Playwright 1.58.2](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/package-lock.json#L2568-L2575) e [Zod 3.25.76](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/package-lock.json#L3147-L3153).

Questa è una decisione prudenziale: il server è un adapter verso endpoint Garmin Connect `gc-api` non documentati e restituisce i JSON remoti come `unknown`, senza output schema o mapping stabile. La sua suite live verifica soltanto poche sentinelle strutturali (`activityId`, `summaryDTO`, `metricDescriptors`, `lapDTOs` e cinque zone), non i campi necessari al coach ([test attività](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/test.ts#L198-L251)). Il contratto interno del coach deve quindi essere più stretto del contratto upstream.

## Confine di sicurezza

Il processo MCP upstream registra insieme tutti i tool e tutte le risorse workout su uno stesso server stdio ([bootstrap](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/index.ts#L7-L18)). Le registrazioni usano `server.tool(name, description, inputShape, handler)` senza annotazioni `readOnlyHint` e senza `outputSchema` ([inizio del registro](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L44-L153)). Inoltre le annotazioni MCP sono solo hint e non una barriera di sicurezza; la specifica dichiara `readOnlyHint` falso per default e avverte i client di non basare su annotazioni non fidate le decisioni d'uso ([MCP ToolAnnotations](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2025-06-18/schema.ts#L1322-L1368)).

Di conseguenza:

- soltanto il gateway possiede il trasporto verso il processo upstream;
- agenti, planner e CLI non ricevono il server Garmin come MCP disponibile;
- il gateway confronta a startup versione e insieme dei tool con una manifest attesa; un tool nuovo resta negato;
- ogni richiesta sconosciuta o non allowlisted fallisce **prima** di raggiungere il trasporto;
- le risorse `workout://...` non vengono inoltrate: sono template per creare workout e non servono alla lettura ([registro risorse](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/resources.ts#L374-L403)).

## Inventario della revisione

La revisione espone **41 tool**. “GET remoto” significa che il codice chiama `GarminClient.get`/`getBytes`; non implica che il tool appartenga allo scope del coach. Il client esegue richieste browser verso `/gc-api/...`, accetta solo HTTP 200/204 e fa `JSON.parse` del corpo senza schema ([implementazione GET](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/garmin-client.ts#L127-L205)).

| Classe | Tool | Policy del coach |
| --- | --- | --- |
| Sessione, nessuna scrittura Garmin | `check-session` | Interno al gateway, ammesso |
| Attività, GET remoto | `list-activities`, `get-activity`, `get-activity-details`, `get-activity-splits`, `get-activity-hr-zones`, `get-activity-polyline`, `get-activity-weather` | Primi cinque ammessi; polyline e weather fuori dall'MVP |
| Profilo/statistiche sportive, GET remoto | `get-user-profile`, `get-personal-records`, `get-fitness-stats`, `get-vo2max`, `get-hr-zones-config`, `get-power-zones` | Solo zone HR/power nell'allowlist MVP; VO2max opzionale e isolato; gli altri non necessari |
| Daily/health, GET remoto | `get-daily-summary`, `get-daily-heart-rate`, `get-daily-stress`, `get-daily-summary-chart`, `get-daily-intensity-minutes`, `get-daily-movement`, `get-daily-respiration` | Negati: fuori scope e possibile contaminazione recovery |
| Sonno/recovery Garmin, GET remoto | `get-sleep`, `get-body-battery`, `get-hrv`, `get-training-readiness`, `get-sleep-stats` | **Vietati senza eccezioni** |
| Altri dati personali, GET remoto | `get-weight`, `get-calendar`, `get-goals`, `get-badges`, `get-badge-leaderboard`, `get-hydration` | Negati: fuori scope/minimizzazione dati |
| Workout, GET remoto | `list-workouts`, `get-workout` | Negati: il piano locale non deve leggere né dipendere dal catalogo workout Garmin |
| Download con scrittura locale | `download-fit`, `download-workout-fit` | Negati al gateway: fanno `mkdirSync`/`writeFileSync`, quindi non sono strettamente read-only rispetto all'ambiente ([download attività](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L277-L313), [download workout](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L747-L768)) |
| Mutazione Garmin | `create-workout`, `schedule-workout`, `delete-workout` | **Vietati**; chiamano rispettivamente POST, POST e DELETE ([handler mutativi](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L771-L911)) |
| Provisioning/test | `garmin-login`, `run-tests` | Negati al runtime: login istruisce a scrivere la sessione; il piano di test ordina anche create/schedule/delete ([login](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L44-L103), [run-tests](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L917-L974)) |

L'elenco Daily/health e quello sleep/recovery sono separati intenzionalmente: alcuni tool Daily non si chiamano “recovery”, ma descrizioni ed endpoint includono resting HR, stress, wellness e respiration ([Daily Health](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L320-L431)); non devono entrare nel modello quando Whoop è l'unica fonte recovery. I cinque tool esplicitamente recovery leggono servizi sleep, body battery, HRV e training readiness ([sleep/HRV](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L438-L480), [training readiness/sleep stats](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L588-L619)).

## Allowlist minima

La manifest MVP consigliata è:

```json
{
  "upstream_package": "@etweisberg/garmin-connect-mcp@0.1.23",
  "upstream_commit": "87d0ea059fb67f1ce65ac05100df74c3c3777c84",
  "tools": [
    "check-session",
    "list-activities",
    "get-activity",
    "get-activity-details",
    "get-activity-splits",
    "get-activity-hr-zones",
    "get-hr-zones-config",
    "get-power-zones"
  ]
}
```

`check-session` è una health check privata. Le altre sette operazioni coprono inventario, riepilogo, serie temporali, lap e configurazione di intensità per running e cycling. Gli endpoint e input effettivi sono definiti nel registro attività ([attività](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L135-L225)) e nelle configurazioni zone ([zone HR/power](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L573-L583)).

`get-vo2max` può essere abilitato in una seconda manifest soltanto quando il mapper dimostra con fixture reali come distinguere il valore running da quello cycling. `get-fitness-stats` e `get-personal-records` non sono necessari: volume, durata e record osservati si possono derivare dalle attività validate, evitando un secondo payload non tipizzato. Il codice di `get-fitness-stats` accetta stringhe libere per `aggregation` e `metric` e impone internamente `userFirstDay: "sunday"`, quindi non è un fondamento adatto alla semantica Europe/Rome del coach ([fitness stats](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L526-L555)).

## Contratto reale dei payload e mapping

### Vincoli osservabili upstream

- Tutti i risultati dati sono un singolo content block di testo contenente JSON pretty-printed; non c'è `structuredContent` né validazione dell'output ([helper `jsonResult`](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L12-L25)).
- `list-activities(limit=20,start=0)` offre solo paginazione a offset; non offre intervallo date né filtro sport. Le descrizioni “1-100” non sono vincoli Zod `.min/.max` ([schema list](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L135-L153)). L'import deve paginare, validare ogni elemento, filtrare localmente la finestra e mantenere solo running/cycling.
- La sola garanzia testata per la lista è “array non vuoto” e la presenza di `activityId` sull'elemento usato per il bootstrap. Nessun nome campo sportivo è sotto test ([bootstrap](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/test.ts#L604-L618)).
- `get-activity(activityId)` restituisce il JSON raw dell'endpoint e la suite richiede soltanto `summaryDTO`. Il mapper deve cercare identità, tipo sport, tempi, distanza, HR, cadenza, quota e potenza in una fixture catturata dalla versione fissata; non può considerarli garantiti dalla TypeScript API.
- `get-activity-details(activityId,maxChartSize=10000)` forza `maxPolylineSize=0` e `maxHeatMapSize=2000`. La suite richiede `metricDescriptors`, mentre il piano testuale parla genericamente di “metricDescriptors + metrics” ([handler details](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L172-L191)). Il mapper deve associare ogni serie al relativo descriptor, mai a una posizione fissa, e deve tollerare metriche assenti.
- `get-activity-splits` ha come unica sentinella `lapDTOs`; `get-activity-hr-zones` è testato come array di cinque elementi e il piano di test nomina `secsInZone`. Non esistono tipi per i campi interni ([handler splits/zones](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/src/tools.ts#L194-L225)).
- Il server non dichiara unità per i payload attività. Non è quindi lecito assumere solo dal nome che distanza, durata, velocità, potenza o cadenza abbiano una determinata unità. Le conversioni SI devono essere convalidate da fixture reali e registrate con `source_field`, `source_unit`, `canonical_unit` e versione del mapper.

### Regole del mapper interno

1. Salvare `activityId` come `source_id` stringa e conservare separatamente timestamp originale, timezone/offset se presenti e `imported_at` Europe/Rome.
2. Classificare lo sport da un valore raw osservato e versionato (per esempio una chiave dentro l'activity type), con tabella esplicita `raw -> running|cycling|other`; device name/model non decide lo sport.
3. Accettare un'attività nella pipeline running/cycling soltanto quando ID, sport e start time sono validi. Campi numerici opzionali mancanti restano `null` con quality `partial`, mai zero.
4. Estrarre summary, serie e lap in strutture distinte; deduplicare sul source ID e non sul titolo/data.
5. Per le serie, risolvere descriptor e sample insieme; se cardinalità o tipo non coincidono, conservare evidenza raw in quarantena e marcare `suspect`.
6. Applicare una denylist ricorsiva prima di persistenza normalizzata e prima dei prompt: sleep/score/stages, HRV, body battery, training readiness, recovery time, daily stress, resting HR, respiration/Pulse Ox notturni e loro alias. Un campo vietato comparso in un payload attività è scartato e genera un evento di audit.
7. Conservare i payload raw solo nello storage d'ingestione protetto e con retention separata; nessun agente riceve raw JSON Garmin.

Non è possibile fissare onestamente una tabella campo-per-campo running/cycling dalla sola API upstream: il repository non contiene fixture di attività, interfacce di risposta o OpenAPI e i test live dipendono dall'account Garmin. La specifica futura deve includere una **sessione di capture contrattuale** con un'attività sintetica/consentita di corsa e una di ciclismo dell'utente, redatte e trasformate in fixture anonime. Finché quelle fixture non esistono, i soli campi garantiti sono le sentinelle sopra; tutto il resto è “candidate field”, non contratto.

## Test di accettazione del gateway

- La manifest contiene esattamente gli otto tool indicati e nessun wildcard/prefisso.
- Ogni nome non allowlisted, inclusi i tre tool mutativi e tutti i tool Garmin recovery, restituisce `DENIED_TOOL` e un fake upstream registra zero chiamate.
- Un diff della lista tool upstream non amplia mai l'allowlist; una versione/hash inattesi bloccano l'avvio finché la manifest non viene revisionata.
- Date, ID, offset e limiti sono validati dal gateway con schema stretto; `limit` è intero 1–100 e `maxChartSize` ha un tetto configurato.
- Le fixture running e cycling verificano sport mapping, unità, nullable fields, descriptor/series, lap e provenance.
- Fixture avversarie contenenti metriche Garmin recovery dimostrano che nessun campo vietato raggiunge database normalizzato o prompt.
- Gli agenti runtime non vedono né il server upstream né le risorse workout; l'audit conserva tool logico, tool upstream, timestamp, esito, versione e hash degli input senza credenziali.

## Conseguenze

La decisione rende possibile progettare ingestione e schema normalizzato senza fingere che l'API Garmin Connect sia stabile. Introduce però un gate necessario prima dell'implementazione completa del mapper: catturare e anonimizzare due payload reali sulla versione fissata. Qualunque upgrade di `garmin-connect-mcp` richiede inventario tool, diff endpoint/schema, rigenerazione fixture e revisione esplicita della manifest; non basta aggiornare la dipendenza.
