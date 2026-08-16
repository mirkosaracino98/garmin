# Percorso di accesso ai dati WHOOP per l'MVP

Stato della ricerca: 16 agosto 2026. Fonti consultate: esclusivamente documentazione ufficiale WHOOP.

## Decisione

Usare **WHOOP Developer API v2** come unico percorso di acquisizione dell'MVP. L'adapter deve effettuare pull incrementali delle collezioni `recovery`, `sleep` e `cycle` con OAuth 2.0 e gli scope minimi `read:recovery`, `read:sleep`, `read:cycles` e `offline`. Non richiedere `read:workout`, `read:profile` o `read:body_measurement` nell'MVP.

CSV e inserimento manuale non sono fallback automatici dell'MVP. Restano implementazioni future possibili della stessa porta di dominio se l'API non fosse più utilizzabile. In assenza di import API valido il coach deve marcare WHOOP come mancante e applicare la policy conservativa già fissata, senza usare Garmin.

Questa scelta massimizza l'automazione del ciclo settimanale senza sacrificare i campi richiesti. Un'app può essere usata immediatamente in sviluppo da un massimo di 10 membri, quindi il singolo utente dell'app personale non richiede l'approvazione pubblica di WHOOP ([App Approval](https://developer.whoop.com/docs/developing/app-approval/)).

## Confronto

| Criterio | API ufficiale v2 | Export CSV | Inserimento manuale |
| --- | --- | --- | --- |
| Autenticazione / avvio | Richiede membership WHOOP, app nel Developer Dashboard, Client ID/Secret, redirect URI e consenso OAuth 2.0. Lo scope `offline` restituisce refresh token ([Overview](https://developer.whoop.com/docs/developing/overview/), [OAuth 2.0](https://developer.whoop.com/docs/developing/oauth/)). | L'utente avvia l'export dall'app WHOOP, conferma l'email e scarica il link ricevuto ([How to Export Your Data](https://support.whoop.com/s/article/How-to-Export-Your-Data?language=en_US)). | Nessuna integrazione WHOOP da autenticare; l'utente trascrive nel coach valori visualizzati altrove. Questa è una proprietà del nostro input locale, non una funzione documentata da WHOOP. |
| Campi utili | Copre recovery score, HRV RMSSD, RHR; sonno e stadi, performance, consistency, efficiency e respiratory rate; day strain dai cicli ([API reference](https://developer.whoop.com/api/), [Recovery](https://developer.whoop.com/docs/developing/user-data/recovery/), [Sleep](https://developer.whoop.com/docs/developing/user-data/sleep/), [Cycle](https://developer.whoop.com/docs/developing/user-data/cycle/)). | I CSV standard includono recovery, RHR, HRV, strain, sonno e stadi, sleep performance/efficiency e respiratory rate; dunque coprono i campi necessari ([How to Export Your Data](https://support.whoop.com/s/article/How-to-Export-Your-Data?language=en_US)). | Può coprire soltanto i campi che chiediamo e che l'utente trova; granularità e completezza dipendono dalla trascrizione. |
| Limiti | Collezioni paginate; `recovery` e `cycle` hanno al massimo 25 record per pagina. Limiti predefiniti: 100 richieste/minuto e 10.000/giorno; superandoli arriva `429` ([API reference](https://developer.whoop.com/api/), [Pagination](https://developer.whoop.com/docs/developing/pagination/), [Rate Limiting](https://developer.whoop.com/docs/developing/rate-limiting/)). | Preparazione dichiarata entro 24 ore; link valido 7 giorni. Non è un canale incrementale ([How to Export Your Data](https://support.whoop.com/s/article/How-to-Export-Your-Data?language=en_US)). | Nessun rate limit tecnico, ma costo umano quotidiano/settimanale e rischio di omissioni. Quest'ultima è un'inferenza operativa. |
| Affidabilità | Dati strutturati, timestamp e ID sorgente; gli stati `SCORED`, `PENDING_SCORE`, `UNSCORABLE` rendono esplicita l'assenza temporanea o definitiva dello score. Occorre gestire `401`, `429`, `500`, paginazione e aggiornamenti tardivi ([Recovery](https://developer.whoop.com/docs/developing/user-data/recovery/), [API reference](https://developer.whoop.com/api/)). | Formato strutturato ma consegna asincrona e procedura manuale ripetuta: adatto a bootstrap/recupero storico, debole per un closed loop settimanale. La valutazione è un'inferenza dai tempi documentati. | Nessuna dipendenza runtime dall'API, ma nessuna garanzia meccanica contro errori di trascrizione o date mancanti. |
| Privacy | Consenso per scope; token e segreti locali. WHOOP prescrive di non registrare/condividere il Client Secret e permette di revocare l'accesso. I termini API impongono protezione delle credenziali e conformità privacy ([Getting Started](https://developer.whoop.com/docs/developing/getting-started/), [OAuth 2.0](https://developer.whoop.com/docs/developing/oauth/), [API Terms](https://developer.whoop.com/api-terms-of-use/)). | WHOOP dichiara che gli export sanitari sono cifrati, ma il file e il link email devono poi essere custoditi dall'utente ([How to Export Your Data](https://support.whoop.com/s/article/How-to-Export-Your-Data?language=en_US)). | Riduce segreti e traffico di integrazione, ma i valori personali devono comunque essere salvati localmente dal coach. |
| Sostituibilità | Alta se il mapping WHOOP resta dietro la porta `get_recovery_window`; il dominio non deve dipendere da DTO, scope o ID WHOOP. | Alta: un adapter CSV può produrre lo stesso contratto, ma le colonne vanno versionate e validate. | Alta: un adapter manuale può produrre lo stesso contratto con qualità `partial` e provenance `manual`. |

## Contratto minimo dell'adapter API

Per ogni finestra richiesta, l'adapter deve:

1. leggere `/developer/v2/recovery`, `/developer/v2/activity/sleep` e `/developer/v2/cycle` usando `start`, `end` e `nextToken`;
2. correlare recovery e sleep tramite `sleep_id` e il ciclo tramite `cycle_id`, conservando gli identificatori WHOOP soltanto nella provenance;
3. importare almeno `recovery_score`, `resting_heart_rate`, `hrv_rmssd_milli`, durata totale del sonno derivata dagli stadi, `sleep_performance_percentage`, `respiratory_rate` e day `strain`;
4. conservare `created_at`, `updated_at`, intervallo osservato, timezone originale e `score_state`;
5. produrre un'osservazione `partial` o `missing`, non valori sintetici, quando `score_state` è `PENDING_SCORE`/`UNSCORABLE` o il record correlato manca;
6. riesaminare una piccola sovrapposizione temporale a ogni pull e fare upsert idempotente, perché i record espongono `updated_at` e possono essere ricalcolati;
7. calcolare localmente trend e baseline: l'API documenta osservazioni e score, non un endpoint stabile per una “baseline WHOOP” pronta all'uso.

I punti 6 e 7 sono decisioni progettuali inferite dai contratti ufficiali, non garanzie del provider.

## Autenticazione e segreti

- Eseguire una sola autorizzazione interattiva iniziale con Authorization Code flow. Il redirect URI deve essere preregistrato e coincidere con quello della richiesta ([Getting Started](https://developer.whoop.com/docs/developing/getting-started/)).
- Richiedere soltanto `read:recovery read:sleep read:cycles offline`. WHOOP raccomanda di limitare gli scope a quelli realmente usati ([Getting Started](https://developer.whoop.com/docs/developing/getting-started/)).
- Conservare Client Secret, access token e refresh token fuori dal repository e dagli output. Il refresh ruota sia access token sia refresh token: una seconda richiesta concorrente con il vecchio refresh token fallisce ([OAuth 2.0](https://developer.whoop.com/docs/developing/oauth/)).
- Serializzare il refresh e sostituire atomicamente entrambi i token. L'esempio ufficiale restituisce `expires_in: 3600`, mentre il codice deve rispettare sempre il valore ricevuto ([OAuth 2.0](https://developer.whoop.com/docs/developing/oauth/)).
- Fornire un comando locale per revocare l'integrazione tramite `DELETE /developer/v2/user/access` e cancellare i token locali ([API reference](https://developer.whoop.com/api/)).

## Affidabilità operativa

Per il CLI locale non usare webhooks nell'MVP: richiedono un endpoint HTTPS pubblico e WHOOP chiarisce che possono essere duplicati o persi; raccomanda comunque una riconciliazione via API ([Webhooks](https://developer.whoop.com/docs/developing/webhooks/)). Un pull a setup, prima della review settimanale e su richiesta è sufficiente per un singolo utente e resta molto sotto i limiti pubblicati.

Retry limitati sono appropriati per `429` e `5xx`, rispettando gli header `X-RateLimit-*`; `401` deve tentare un solo refresh serializzato e poi richiedere nuova autorizzazione. Un fallimento non deve riutilizzare silenziosamente l'ultima osservazione come se fosse corrente: il dato può essere mantenuto storicamente, ma la finestra richiesta deve dichiarare freshness e qualità.

## Conseguenze per la specifica

- Implementare nell'MVP un solo `WhoopApiAdapter`; non implementare insieme CSV e manuale.
- Fissare l'integrazione alla v2 e aggiungere contract test basati sull'OpenAPI ufficiale, includendo paginazione e i tre `score_state`.
- Tenere DTO API e token fuori dal dominio. La porta rimane `get_recovery_window(start_date, end_date) -> RecoveryObservation[]`, così un futuro `WhoopCsvAdapter` o `WhoopManualAdapter` non cambia Feature Engine o Recovery Expert.
- Non acquisire workout WHOOP: Garmin resta la fonte delle attività, mentre `read:cycles` serve unicamente per il day strain WHOOP.
- Considerare CSV come procedura esplicita di migrazione/bootstrap futura, non come fallback automatico. Mescolare fonti nella stessa finestra senza una regola di precedenza indebolirebbe provenance e deduplicazione.
- Riesaminare i [termini API WHOOP](https://developer.whoop.com/api-terms-of-use/) prima di qualsiasi distribuzione o passaggio da uso personale a prodotto; questa ricerca non esprime una conclusione legale.

## Verifica della decisione

Prima di chiudere l'implementazione dell'adapter, eseguire uno smoke test con l'account reale: autorizzare gli scope minimi, importare 8–12 settimane, verificare presenza e unità dei sette campi minimi, controllare almeno un record non `SCORED` e provare refresh/revoca. Se uno dei campi obbligatori non è disponibile per l'account/dispositivo concreto, registrarlo come dato mancante; non ampliare automaticamente gli scope e non introdurre Garmin come fallback.
