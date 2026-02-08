
configuration file: containing all Peer-IDs and their corresponding IP-Addresses and port numbers

# General connection

* + Peers must be able to receive their own messages
* + Peers must not be able to receive messages from sources outside the group

* + Peers must have a unique Peer-ID
* Users must be able to configure the Peer-ID via a command line argument
* Peers must not be able to detect and handle multiple Peers with the same Peer-ID

* Users must be able to pass the path to a config file as argument
* Peers must not be able to handle changing IP-Addresses (static group)

* Peers must be able to reach other Peers via UDP

* Peers must be able to handle an any number of peers (default is 5)

# General

* Messages must be sent with a Message-ID
* The Message-ID must be created out of the Peer-ID and a continuous sequence number

# UI

* The UI must be available via the command line
* The UI must be text based
* The UI must be interactive

* The UI must be in english

* The UI must allow the user to enter an arbitrary payload with a freely defined maximum length which is sent to all Peers

* The UI must be able to save received payload, including the message-ID, in the order of receiving in a log file

* The UI must be able to parse the configuration file and change the config (peers.txt)

* The UI must be able to accept the following flags on startup:
  * Peer-ID of the peer
  * portnumber of the peer
  * path to log file
  * path to config file
  * declarations about error injection
* The user must declare the message-ID and the index of the bit that should be flipped when using the error injection

# Middleware

* The middleware must be able to support a reliable group communication using the requirements of the scriptum (integrity, validity, agreement) via iterative multicast emulation
* The middleware must use Stop and Wait ARQ in their peer to peer connections
* The middleware must wait a constant time of 1 second to detect failure of the peer

* The middleware must check all incoming messages using the Internet Checksum defined in RFC 1071
* The Internet Checksum must be implemented without using premade functions or libraries

* The middleware must send a maximum of 3 retransmissions during the stop and wait connection

* The middleware must allow the user to test the checksum mechanism by injecting an error into the message
* The middleware must recognize the message with injected error as faulty and drop it.