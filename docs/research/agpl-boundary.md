# Confine di licenza per `garmin-connect-mcp`

Stato della ricerca: 2026-08-16. Upstream esaminato al commit
[`87d0ea0`](https://github.com/etweisberg/garmin-connect-mcp/tree/87d0ea059fb67f1ce65ac05100df74c3c3777c84),
versione npm dichiarata `0.1.23`.

> Questa è una valutazione tecnica di conformità basata sulle fonti indicate, non
> consulenza legale. Il confine fra programmi separati e opera combinata dipende
> dai fatti e, in ultima istanza, è una questione giuridica. Prima di distribuire
> un prodotto commerciale, incorporare codice upstream o offrire un servizio di
> rete, far verificare il caso concreto da un professionista qualificato.

## Decisione

Per l'MVP, mantenere `garmin-connect-mcp` **non modificato, versionato e in un
processo esterno separato**, avviato come eseguibile npm e raggiunto dal coach
solo tramite il protocollo MCP su `stdio`. L'utente installa il pacchetto
upstream separatamente; il repository e gli artefatti distribuibili del coach
non contengono sorgenti, build, fork o moduli importati da
`garmin-connect-mcp`.

Il gateway read-only appartiene al coach e tratta l'MCP come un servizio esterno:

```text
coach + gateway proprietario del progetto
             |
             | MCP standard su stdio (process boundary)
             v
@etweisberg/garmin-connect-mcp non modificato
```

Questa scelta conserva un confine operativo e di licenza chiaro, permette di
tenere il coach sotto una licenza scelta indipendentemente e soddisfa anche il
vincolo di sicurezza read-only. Non è una garanzia assoluta: secondo la guida
GNU, processi che comunicano con pipe/socket/argomenti sono *normalmente*
separati, ma una comunicazione semanticamente molto intima può comunque farli
considerare un unico programma. MCP è qui usato come protocollo tra eseguibili,
senza memoria condivisa, linking o API interne; ritenere i due programmi
separati è quindi una **inferenza prudenziale**, non un fatto espresso dalla
licenza. [GNU GPL FAQ: “Mere Aggregation”](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)

Per preservare il confine:

- non importare package/moduli interni dell'MCP nel processo Python del coach;
- non copiare o vendorizzare sorgenti o file compilati upstream nel repository;
- non applicare patch a runtime e non mantenere un fork per l'MVP;
- scambiare soltanto richieste/risposte MCP documentate, senza condividere
  memoria o strutture interne del processo;
- fissare versione e provenienza nella configurazione/dependency inventory, ma
  lasciare installazione e aggiornamento dell'MCP come passo separato;
- non includere il pacchetto MCP nel wheel, eseguibile, container o installer
  del coach. Se in futuro serve un bundle, trattarlo esplicitamente come scenario
  di distribuzione descritto sotto.

## Fatti verificati

### Licenza e attribuzioni upstream

- Il repository identifica `garmin-connect-mcp` come AGPL-3.0; `package.json`
  dichiara `"license": "AGPL-3.0"` e un binario separato
  `garmin-connect-mcp` basato su `dist/index.js`.
  [package.json upstream](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/package.json)
- Il file `LICENSE` attribuisce il copyright 2026 a Ethan Weisberg e concede
  ridistribuzione/modifica secondo AGPL v3 o successiva.
  [LICENSE upstream](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/LICENSE)
- Il file `NOTICE` dichiara che il progetto contiene codice da
  `Taxuspt/garmin_mcp`, con copyright 2025 Alexandre Domingues sotto MIT; la MIT
  richiede che copyright e permission notice siano inclusi nelle copie o
  porzioni sostanziali.
  [NOTICE upstream](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/NOTICE)
- Il README documenta proprio l'esecuzione come server MCP esterno tramite
  `npx @etweisberg/garmin-connect-mcp` e un trasporto MCP `stdio`.
  [README upstream](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/README.md)

### Cosa attiva gli obblighi AGPL

- Eseguire il programma non è limitato dalla licenza; la AGPL pone condizioni
  su modifica e propagazione/conveying. La licenza definisce “convey” come una
  propagazione che consente ad altre parti di fare o ricevere copie; la sola
  interazione in rete senza trasferire una copia non è conveying.
  [AGPL §§2 e 0](https://www.gnu.org/licenses/agpl-3.0.en.html#section2)
- Copiare e distribuire sorgente non modificato richiede mantenere gli avvisi,
  conservare gli avvisi di assenza di garanzia e consegnare una copia della
  licenza.
  [AGPL §4](https://www.gnu.org/licenses/agpl-3.0.en.html#section4)
- Distribuire una versione modificata richiede, fra l'altro, evidenziare le
  modifiche e le date, licenziare l'intera opera coperta sotto AGPL e preservare
  gli avvisi legali appropriati.
  [AGPL §5](https://www.gnu.org/licenses/agpl-3.0.en.html#section5)
- Distribuire object code richiede rendere disponibile il *Corresponding Source*
  in uno dei modi ammessi dalla sezione 6. Il sorgente corrispondente è la forma
  preferita per modificare l'opera e comprende quanto necessario a generare,
  installare ed eseguire l'object code, salvo le eccezioni previste.
  [AGPL §§1 e 6](https://www.gnu.org/licenses/agpl-3.0.en.html#section6)
- Se una **versione modificata** supporta interazione remota su una rete, deve
  offrire in modo evidente a tutti gli utenti remoti il Corresponding Source,
  gratuitamente e tramite un mezzo standard. Questa è la condizione specifica
  della AGPL rispetto alla GPL.
  [AGPL §13](https://www.gnu.org/licenses/agpl-3.0.en.html#section13)

## Conseguenze per scenario

### 1. Uso personale locale

Installare ed eseguire la release upstream non modificata sul proprio computer,
senza darne copie ad altri e senza offrire una versione modificata attraverso la
rete, non impone di pubblicare il coach né il proprio codice. Anche modifiche
tenute esclusivamente per sé non devono essere pubblicate solo perché esistono;
la FAQ GNU conferma che le modifiche private non devono essere rilasciate.
[GNU GPL FAQ: modifiche private](https://www.gnu.org/licenses/gpl-faq.en.html#GPLRequireSourcePostedPublic)

Scelta operativa: registrare comunque nome, versione, URL, licenza e notice in
`LICENSES.md`/SBOM. È buona igiene e rende riproducibile l'installazione, ma non è
un “source offer”. Segreti Garmin e dati atleta non fanno parte del sorgente e
non devono essere pubblicati.

### 2. Distribuzione del solo coach

Se il coach contiene soltanto il proprio codice e istruisce l'utente a installare
separatamente l'MCP da upstream, non sta consegnando una copia dell'MCP. In base
al significato di “convey” e al confine tra programmi separati, **inferiamo** che
gli obblighi AGPL dell'MCP non si estendano al coach.

Documentare comunque la dipendenza esterna e l'attribuzione, ad esempio:

```text
Optional external runtime dependency:
@etweisberg/garmin-connect-mcp 0.1.23 — AGPL-3.0-or-later
Copyright (C) 2026 Ethan Weisberg
https://github.com/etweisberg/garmin-connect-mcp
Includes MIT-licensed code copyright (c) 2025 Alexandre Domingues;
see the upstream NOTICE.
```

Non affermare che il pacchetto è incluso se non lo è, e non copiare il testo
upstream nel prodotto oltre agli avvisi necessari. Il link alla sorgente
upstream è informativo, non sostituisce gli obblighi se in futuro si distribuisce
effettivamente una copia.

### 3. Bundle o redistribuzione dell'MCP non modificato

Se installer, container, archivio o immagine del coach contiene anche l'MCP,
si sta distribuendo object code AGPL. È possibile mantenere il coach separato
come parte indipendente di un aggregato, ma per la parte MCP occorre almeno:

1. includere copyright e avvisi upstream, il `NOTICE` MIT e il testo completo
   della AGPL;
2. indicare chiaramente che la parte MCP è AGPL e priva di garanzia;
3. fornire il Corresponding Source della **versione esatta distribuita** con una
   modalità conforme alla sezione 6;
4. non imporre EULA o misure che limitino i diritti AGPL dei destinatari.

La via meno ambigua è distribuire insieme il sorgente corrispondente completo,
oppure offrire nello stesso luogo di download accesso equivalente e gratuito al
sorgente mantenuto disponibile finché si distribuisce l'object code. Un semplice
link al repository `main` non basta a garantire la corrispondenza futura con il
binario. La FAQ GNU specifica che servono i sorgenti completi corrispondenti, non
solo diff o una versione upstream generica.
[GNU GPL FAQ: sorgente del binario modificato](https://www.gnu.org/licenses/gpl-faq.en.html#DistributeExtendedBinary)

Una “offerta scritta” valida almeno tre anni è solo una delle opzioni della
sezione 6; non è necessaria se il sorgente viene fornito con una modalità diversa
già conforme. Per questo progetto è preferibile evitare l'offerta scritta e
fornire direttamente sorgente/versione riproducibile.

### 4. Modifica o fork dell'MCP

Modificare l'MCP per uso strettamente personale e locale non obbliga di per sé a
pubblicare il fork. Se però la versione modificata viene distribuita:

- marcare in modo evidente i file come modificati e datarli;
- mantenere avvisi, `NOTICE`, testo AGPL e informazioni di assenza di garanzia;
- distribuire l'intera opera coperta sotto AGPL-3.0-or-later;
- fornire il Corresponding Source completo della build distribuita.

Se la versione modificata consente a utenti di interagire da remoto, aggiungere
anche nell'interfaccia un'offerta evidente e gratuita del Corresponding Source
ai sensi della sezione 13. Per prudenza, considerare “utenti remoti” anche utenti
autenticati o interni: la sezione 13 dice “all users”, non soltanto il pubblico.

### 5. Incorporazione nel coach

Copiare file, importare moduli interni, linkare codice o fondere sorgenti rende
molto più probabile che il risultato sia un'unica opera derivata/combinata. In
caso di distribuzione, il risultato dovrebbe quindi essere trattato come coperto
nel suo complesso da AGPL, con Corresponding Source completo. La FAQ GNU
distingue espressamente il semplice affiancamento dall'incorporazione e considera
linking e condivisione di strutture interne forti indizi di un solo programma.
[GNU GPL FAQ: programmi separati e plug-in](https://www.gnu.org/licenses/gpl-faq.en.html#GPLPlugins)

Decisione: **vietare l'incorporazione nell'MVP**. Se diventa necessaria, aprire
una nuova decisione e scegliere una delle seguenti vie prima di scrivere codice:

- accettare AGPL per l'opera combinata e progettare distribuzione/source access;
- ottenere una licenza alternativa esplicita dai titolari dei copyright;
- sostituire l'integrazione con un componente dalla licenza compatibile con gli
  obiettivi di distribuzione.

## Checklist da portare nella specifica

- [ ] Dipendenza esterna pinning esatto (`0.1.23` o successiva versione
      deliberatamente approvata) e processo `stdio` separato.
- [ ] Nessun import, vendoring, patch o fork di `garmin-connect-mcp`.
- [ ] Installazione upstream separata dagli artefatti del coach.
- [ ] `LICENSES.md` o SBOM con AGPL-3.0-or-later, copyright upstream, URL e
      attribuzione MIT del `NOTICE`.
- [ ] CI che verifichi che wheel/container/installer del coach non incorpori il
      pacchetto MCP.
- [ ] Riesame licenze obbligatorio prima di bundle, distribuzione dell'MCP,
      modifica/fork, incorporazione o servizio remoto.
- [ ] Se si distribuisce l'MCP: conservare una copia verificata del sorgente
      corrispondente alla build, testi di licenza/notices e meccanismo §6.
- [ ] Se una modifica dell'MCP è usata via rete: offerta sorgente evidente §13.

## Risposta sintetica

L'uso personale locale dell'MCP non rende pubblico il coach. Per l'MVP, eseguire
l'upstream non modificato come dipendenza installata separatamente e comunicare
via MCP/stdio; attribuirlo nell'inventario licenze. Non incorporare né distribuire
il pacchetto. Se in futuro lo si distribuisce, fornire licenza, notices e sorgente
corrispondente; se lo si modifica e lo si rende accessibile in rete, offrire il
sorgente agli utenti remoti. Un fork o codice incorporato richiede un nuovo
riesame e, salvo licenza alternativa, va trattato come AGPL.

## Fonti primarie

- [`etweisberg/garmin-connect-mcp` LICENSE](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/LICENSE)
- [`etweisberg/garmin-connect-mcp` NOTICE](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/NOTICE)
- [`etweisberg/garmin-connect-mcp` package.json](https://github.com/etweisberg/garmin-connect-mcp/blob/87d0ea059fb67f1ce65ac05100df74c3c3777c84/package.json)
- [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.en.html)
- [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)
