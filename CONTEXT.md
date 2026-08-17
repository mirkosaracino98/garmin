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
