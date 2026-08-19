# AI Running Coach

Un coach locale che combina attività osservate e dichiarazioni dell'atleta per adattare prudentemente un piano di corsa, mantenendo esplicite provenienza e incertezza.

## Language

**Sessione palestra**:
Allenamento di forza dichiarato dall'atleta subito dopo l'esecuzione, descritto minimamente da durata, RPE di sessione e coinvolgimento delle gambe.
_Avoid_: workout di forza, scheda palestra

**Osservazione DOMS**:
Valutazione separata dell'indolenzimento muscolare percepito dall'atleta, dichiarata la mattina successiva alla sessione palestra; non è una proprietà né una previsione della sessione.
_Avoid_: DOMS della sessione, dolore previsto

**Sessione palestra prevista**:
Vincolo ricorrente e fisso di calendario dichiarato dall'atleta per il lunedì o il venerdì, attorno al quale il coach colloca corsa e ciclismo; resta distinto da una sessione palestra eseguita.
_Avoid_: data preferita, sessione spostabile, allenamento completato

**Payload grezzo**:
Risposta originale acquisita da una fonte esterna durante un'importazione, conservata temporaneamente per diagnosi e rinormalizzazione ma non usata direttamente dal coach.
_Avoid_: dato sorgente, dato canonico

**Osservazione normalizzata**:
Rappresentazione canonica e versionata di un fatto acquisito, con provenienza e qualità esplicite; è l'input persistente dei calcoli e delle decisioni del coach.
_Avoid_: payload elaborato, dato pulito

**Attività osservata**:
Osservazione normalizzata dei dati complessivi di una singola attività acquisita, distinta dagli split, dall'esposizione alle zone e dalle configurazioni usate per interpretarla.
_Avoid_: attività aggregata, payload attività

**Split osservato**:
Osservazione normalizzata di un lap registrato all'interno di un'attività osservata, identificato nella sequenza originale e collegato all'attività senza esservi annidato.
_Avoid_: split summary, intervallo pianificato

**Esposizione a zone**:
Osservazione normalizzata del tempo trascorso nelle zone di intensità durante una specifica attività; non definisce le soglie delle zone.
_Avoid_: configurazione zone, intensità prevista

**Configurazione zone**:
Osservazione normalizzata e temporalmente identificata delle soglie HR o potenza acquisite dal profilo sportivo; resta distinta dall'esposizione prodotta da un'attività.
_Avoid_: esposizione a zone, zone dell'attività

**Qualità dell'osservazione**:
Classificazione deterministica della completezza e affidabilità strutturale di un'osservazione normalizzata (`complete`, `partial`, `suspect` o `missing`), accompagnata da diagnostiche strutturate; non esprime la confidenza di un segnale o di una decisione del coach.
_Avoid_: confidenza, attendibilità atletica, qualità del piano

**Revisione di osservazione**:
Versione immutabile di un'osservazione logica già acquisita, creata quando la fonte cambia il fatto associato alla stessa identità; una sola revisione è corrente, mentre le precedenti restano tracciabili.
_Avoid_: duplicato, nuova attività, migrazione dello schema

**Segnale derivato**:
Risultato rigenerabile calcolato da osservazioni normalizzate mediante una regola identificata e versionata.
_Avoid_: dato normalizzato, osservazione, verdetto

**Proposta generativa**:
Contributo strutturato e non autoritativo prodotto da un modello linguistico a partire da evidenze minimizzate; non può sostituire osservazioni, segnali derivati o vincoli deterministici.
_Avoid_: decisione del coach, piano LLM, verdetto del modello

**Esito degradato**:
Risultato esplicitamente incompleto prodotto senza una proposta generativa, che conserva evidenze e vincoli deterministici e richiede revisione umana quando non esiste già un piano valido.
_Avoid_: fallback LLM, piano completo, errore silenzioso

**Profilo di carico**:
Segnale derivato multidimensionale che mantiene distinti il carico sistemico interno, il carico esterno specifico dello sport e il carico neuromuscolare sulle gambe; non implica equivalenza tra sport.
_Avoid_: carico totale, chilometri equivalenti, punteggio universale

**Carico sistemico interno**:
Componente del profilo di carico che rappresenta la risposta complessiva dell'atleta a una sessione, derivata in ordine di preferenza dall'esposizione a zone cardiache, dall'RPE dichiarato o da un intervallo basato sulla sola durata.
_Avoid_: stress totale, Training Effect, carico Garmin

**Carico esterno specifico**:
Componente del profilo di carico che descrive il lavoro osservabile nel linguaggio proprio dello sport, senza convertirlo in un'unità equivalente di un altro sport.
_Avoid_: chilometri equivalenti, carico multisport convertito

**Carico neuromuscolare sulle gambe**:
Componente del profilo di carico che rappresenta l'impegno locale dichiarato delle gambe in una sessione palestra, distinta sia dal carico sistemico sia dalla successiva osservazione DOMS.
_Avoid_: carico palestra totale, DOMS previsto, chilometri palestra

**Intervallo di carico**:
Stima prudente delimitata da un minimo osservato e da un limite superiore, accompagnata da confidenza esplicita quando le evidenze di carico sono incomplete.
_Avoid_: carico imputato, valore esatto, dato mancante sostituito

**Minuti di carico**:
Indice convenzionale del carico sistemico interno ottenuto ponderando ogni minuto osservato per una fascia d'intensità da uno a cinque; rende confrontabili metodi di osservazione diversi senza dichiarare una misura fisiologica.
_Avoid_: TRIMP, TSS, calorie, misura fisiologica

**Discordanza di carico**:
Condizione esplicita in cui due evidenze valide della stessa sessione indicano fasce d'intensità distanti almeno due livelli; nessuna delle due viene mediata o scartata silenziosamente.
_Avoid_: errore del sensore, media dei segnali, dato sospetto

**Copertura del carico**:
Quota della durata osservata in una finestra per cui il carico sistemico dispone di frequenza cardiaca o RPE validi, distinta dalla completezza dell'acquisizione delle attività.
_Avoid_: qualità dell'osservazione, confidenza del piano, completezza dei dati

**Target prescrittivo**:
Intervallo personale che l'atleta deve cercare di seguire durante una parte della seduta; la metrica scelta dipende dall'intento e deve essere affidabile per quel contesto.
_Avoid_: riferimento, valore osservato, obiettivo generico

**Guardrail di intensità**:
Limite complementare usato per impedire che la seduta tradisca il proprio intento quando il target prescrittivo non racconta tutta la risposta dell'atleta.
_Avoid_: secondo target, media dei segnali, verdetto di sicurezza

**Riferimento descrittivo**:
Intervallo mostrato per orientare o interpretare la seduta senza richiederne il rispetto; non determina da solo il completamento dell'intento.
_Avoid_: target prescrittivo, limite, dato irrilevante

**Seduta pianificata**:
Unità immutabile di una versione approvata del piano, identificata da intento, sport, collocazione prevista e criteri di esecuzione; resta riconoscibile anche quando viene spostata o sostituita.
_Avoid_: attività prevista, workout Garmin, seduta completata

**Bozza di piano**:
Versione proposta dal coach che può includere adattamenti automatici ma non governa l'allenamento finché l'atleta non la approva integralmente.
_Avoid_: piano automatico, piano attivo, piano approvato

**Versione approvata del piano**:
Versione della bozza accettata esplicitamente dall'atleta e usata come riferimento corrente per sedute, matching e revisioni successive.
_Avoid_: bozza, proposta, piano generato

**Conferma specifica**:
Accettazione esplicita di un singolo cambiamento importante richiesta prima dell'approvazione complessiva della bozza; resta distinta dalla conferma finale dell'intera versione.
_Avoid_: approvazione implicita, conferma automatica, approvazione del piano

**Adattamento automaticamente proponibile**:
Modifica entro policy che il coach può inserire in una bozza senza conferma specifica, ma che resta inattiva fino all'approvazione finale dell'atleta.
_Avoid_: adattamento automatico, modifica applicata, auto-approvazione

**Seduta impegnativa**:
Seduta running o cycling che occupa uno dei due slot settimanali di stress elevato per intensità, struttura o durata relativa; una corsa lunga facile vi rientra solo quando il suo profilo la rende impegnativa.
_Avoid_: allenamento importante, seduta chiave, qualsiasi lungo

**Limite automatico del lungo**:
Durata massima, dipendente dall'obiettivo running attivo, entro cui il coach può inserire una corsa lunga in una bozza senza conferma specifica; è un guardrail configurabile e non una soglia clinica né un divieto per l'atleta.
_Avoid_: durata sicura, limite medico, lungo massimo assoluto

**Settimana di scarico**:
Settimana pianificata di assorbimento che riduce il volume running e gli slot di stress elevato senza dimostrare tolleranza a un carico superiore.
_Avoid_: settimana persa, settimana facile, settimana tollerata

**Alternativa conservativa giornaliera**:
Variazione temporanea e non persistente che riduce o elimina lo stress della seduta corrente senza modificare la versione approvata del piano.
_Avoid_: adattamento del piano, ripianificazione automatica, nuova versione

**Segnale negativo concordante**:
Condizione prudenziale in cui un trend Whoop sfavorevole rispetto alla baseline personale coincide con almeno un'evidenza indipendente soggettiva, prestativa o di carico; non costituisce una valutazione clinica.
_Avoid_: recovery basso, diagnosi, singolo giorno negativo

**Segnale di interruzione**:
Sintomo dichiarato o osservazione anomala che impone di interrompere la seduta e produce un verdetto di sicurezza bloccato senza formulare diagnosi né idoneità medica.
_Avoid_: red flag, diagnosi automatica, soglia clinica

**Settimana tollerata**:
Finestra di sette giorni con evidenze sufficienti in cui il carico eseguito resta entro l'intervallo approvato e non emergono sintomi o segnali negativi concordanti; una settimana deliberatamente ridotta non dimostra tolleranza a un carico superiore.
_Avoid_: settimana completata, buona settimana, aderenza settimanale

**Corrispondenza piano-esecuzione**:
Segnale derivato e revisionabile che collega una seduta pianificata a un'attività osservata o a una sessione palestra, conservando regola, evidenze, confidenza e interventi manuali; non giudica da solo la qualità dell'esecuzione.
_Avoid_: completamento, aderenza, attività simile

**Esito di esecuzione**:
Valutazione dell'esecuzione di una seduta pianificata rispetto al suo intento e ai suoi criteri, calcolata soltanto dopo una corrispondenza sufficientemente affidabile.
_Avoid_: matching, attività completata, successo della seduta

**Contributo del ciclismo**:
Segnale derivato composto che mantiene distinti il contributo aerobico e la fatica residua di un'attività cycling, senza convertirli in volume o specificità running.
_Avoid_: equivalenza bici-corsa, chilometri equivalenti, saldo ciclismo

**Contributo aerobico del ciclismo**:
Componente del contributo del ciclismo che descrive l'esposizione aerobica osservata nel linguaggio del cycling; può condizionare il piano ma non vale come volume o aderenza running.
_Avoid_: beneficio running, minuti corsa equivalenti, sostituzione automatica

**Fatica residua del ciclismo**:
Componente del contributo del ciclismo che rappresenta quanto la risposta sistemica e l'impegno locale delle gambe possono condizionare le corse successive; resta distinta dal recupero Whoop e dal carico neuromuscolare della palestra.
_Avoid_: recovery cycling, DOMS cycling, carico gambe palestra

**Snapshot decisionale**:
Insieme immutabile delle revisioni correnti di osservazioni e segnali derivati, congelato a un istante di conoscenza e usato come unico input di una revisione del coach o pianificazione.
_Avoid_: stato corrente, copia del database, dati live

**Linea di seduta**:
Continuità dello stesso intento di allenamento attraverso versioni successive del piano; collega istanze immutabili della seduta senza confondere una sostituzione con una modifica.
_Avoid_: seduta pianificata, identificatore della versione, workout ricorrente

**Decisione del coach**:
Esito strutturato e immutabile che applica regole e policy versionate a uno snapshot decisionale, conservando evidenze, incertezza e interventi umani senza incorporare la spiegazione renderizzata.
_Avoid_: proposta generativa, spiegazione, log applicativo

**Risultato obsoleto**:
Segnale, snapshot o stato corrente la cui evidenza è stata revisionata o rimossa e che non può più governare nuove decisioni finché non viene rigenerato o revisionato esplicitamente.
_Avoid_: dato cancellato, errore, ricalcolo automatico

**Manifest dello snapshot**:
Elenco immutabile delle revisioni esatte che compongono uno snapshot decisionale, identificato dal proprio cutoff e da un hash verificabile senza duplicare i valori referenziati.
_Avoid_: copia dei dati, query corrente, cache

**Evidenza di decisione**:
Riferimento esatto e tipizzato a una revisione di osservazione, a un segnale derivato o a un'altra informazione congelata che giustifica una decisione del coach.
_Avoid_: motivazione testuale, dato live, contesto implicito

**Valore non disponibile**:
Esito esplicito e motivato che dichiara l'impossibilità di produrre un valore da evidenze sufficienti; non coincide con zero, `null` o assenza del record.
_Avoid_: dato mancante implicito, valore predefinito, errore silenzioso

**Revisione del coach**:
Valutazione immutabile di uno snapshot decisionale che descrive esecuzione, carico, risposta, lacune e vincoli prima di qualsiasi nuova pianificazione.
_Avoid_: importazione, bozza di piano, revisione di osservazione

**Verdetto di sicurezza**:
Decisione del coach che stabilisce se una bozza è approvabile, richiede attenzione o è bloccata applicando policy e precedenze deterministiche.
_Avoid_: diagnosi, avviso testuale, giudizio LLM

**Piano vigente**:
Unica versione approvata che governa il periodo corrente; resta distinta dalle bozze e può diventare obsoleta o invalidata senza essere riscritta retroattivamente.
_Avoid_: ultimo piano generato, bozza più recente, piano automatico

**Registro di cancellazione**:
Traccia non identificante di una cancellazione esplicita, limitata a operazione, istante e conteggi e priva di valori, identificatori fonte o hash dei dati rimossi.
_Avoid_: backup, payload eliminato, audit completo

**Pacchetto di pianificazione**:
Revisione coerente e approvata atomicamente che riunisce traiettoria verso l'obiettivo, piano di blocco e piano settimanale; soltanto le sedute del piano settimanale governano l'esecuzione.
_Avoid_: singolo file del piano, bozza di piano, piano settimanale

**Traiettoria verso l'obiettivo**:
Vista versionata del percorso macro verso l'obiettivo attivo, distinta sia dal blocco corrente sia dalle sedute eseguibili della settimana.
_Avoid_: piano stagionale vigente, previsione gara, obiettivo

**Piano di blocco**:
Vista versionata delle priorità e della struttura delle successive quattro settimane, priva di autorità esecutiva sulle singole sedute.
_Avoid_: piano mensile, piano settimanale, calendario vigente

**Piano settimanale**:
Componente eseguibile del pacchetto di pianificazione che contiene le sedute pianificate dei successivi sette giorni.
_Avoid_: blocco, bozza, settimana osservata
