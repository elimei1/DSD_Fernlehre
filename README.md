# PET Chat Application

Zuverlässige Gruppenkommunikation und Fehlersimulation.

## Requirements

- Python 3.11+
- Docker-Compose
- Docker running
- blessed library for UI
    * `pip install blessed`

## Schnellstart (Docker)

Die einfachste Methode, das Netzwerk zu starten, ist mittels Docker Compose. Dies startet 5 Peers in einem isolierten Netzwerk.

### Starten
```bash
docker-compose up --build
```
Dies baut das Image und startet die Container (`peer1` bis `peer5`).

### Bedienen eines Peers
Um einen Peer zu steuern, müssen Sie sich mit dessen Container verbinden. Öffnen Sie dazu für jeden Peer ein **neues Terminal-Fenster**:

1.  **Peer 1 verbinden:**
    ```bash
    docker attach peer1
    ```
2.  **Peer 2 verbinden:**
    ```bash
    docker attach peer2
    ```
    *(Wiederholen für weitere Peers nach Bedarf)*

### Beenden

**Beenden:** Geben Sie `/quit` im Chat ein oder stoppen Sie `docker-compose` im Hauptfenster mit `Ctrl+C`.

Um einen Ausfall zu simulieren kann ein speziefischer Container gestoppt werden.
`docker stop peer<1-5>`

---

## Bedienung (TUI)

Die Benutzeroberfläche ist textbasiert und wird über Befehle gesteuert.

Wenn die Applikation über Docker gestartet wird, muss ein Peer zuerst über den Befehl `/setup` konfiguriert werden.

_Dafür müssen die IDs und Ports genau so eingegeben werden wie sie im peers.txt stehen.Eine Abweichung führt zu einem nicht erlaubtem Fehler._

ID: peer_1, Port: 5001, Liste: peers.txt

ID: peer_2, Port: 5002, Liste: peers.txt

ID: peer_3, Port: 5003, Liste: peers.txt

ID: peer_4, Port: 5004, Liste: peers.txt

ID: peer_5, Port: 5005, Liste: peers.txt

### Chatten
Geben Sie einfach eine Nachricht ein und drücken Sie `Enter`. Die Nachricht wird an alle anderen Peers gesendet.

### Befehle
*   `/help`
    Zeigt die verfügbaren Befehle an.
*   `/status`
    Zeigt die eigene **Peer-ID**, den **Port** und die aktuelle **Fehler-Konfiguration** an.
*   `/error <msg_id> <bit_idx>`
    Simuliert einen Bitfehler für einen Integritätstest. Das passiert bei eingehende Nachrichten. Bei uns muss die Peer ID und die Sequence Number zusammen eingegeben werden um zu einer gesamten Message ID zu werden.
    *   `msg_id`: Bestehend aus der Sender ID und der Sequence Number.
    *   `bit_idx`: Der Index des Bits, das gekippt werden soll.
    *   *Beispiel:* `/error peer_12 2` (ID: peer1, Sequence Number: 2, Bit Index: 2)
    *   *Beispiel:* `/error` (verwendet default Werte)
*   `/setup`
    Startet den Konfigurations-Assistenten (nur möglich, wenn der Peer noch unkonfiguriert ist).
*   `/quit`
    Beendet den Peer.

---

## Manuelle Installation (Ohne Docker)

Falls Sie Python direkt nutzen möchten (Requires Python 3.11+):

```bash
python src/main.py --id peer_1 --port 5001 --peers peers.txt --log peer_1.log
```