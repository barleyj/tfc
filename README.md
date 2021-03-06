<img align="right" src="https://cs.helsinki.fi/u/oottela/tfclogo.png" style="position: relative; top: 0; left: 0;">

### Tinfoil Chat

[![Build Status](https://travis-ci.org/maqp/tfc.svg?branch=master)](https://travis-ci.org/maqp/tfc) [![Coverage Status](https://coveralls.io/repos/github/maqp/tfc/badge.svg?branch=master)](https://coveralls.io/github/maqp/tfc?branch=master)

Tinfoil Chat (TFC) is a high assurance encrypted messaging system that
operates on top of existing IM clients. The 
[free and open source software](https://en.wikipedia.org/wiki/Free_and_open-source_software) 
is used together with free hardware to protect users from 
[passive eavesdropping](https://en.wikipedia.org/wiki/Upstream_collection), 
[active MITM attacks](https://en.wikipedia.org/wiki/Man-in-the-middle_attack)
and [remote CNE](https://www.youtube.com/watch?v=3euYBPlX9LM) practised by
organized crime and nation state attackers.

[XSalsa20](https://cr.yp.to/snuffle/salsafamily-20071225.pdf) encryption
and [Poly1305-AES](https://cr.yp.to/mac/poly1305-20050329.pdf) MACs provide
[end-to-end encrypted](https://en.wikipedia.org/wiki/End-to-end_encryption)
communication with [deniable authentication](https://en.wikipedia.org/wiki/Deniable_encryption#Deniable_authentication): Symmetric keys are either 
pre-shared, or exchanged using [X25519](https://cr.yp.to/ecdh/curve25519-20060209.pdf), the public 
keys of which are verified via off-band channel. TFC provides per-message forward secrecy with [hash ratchet](https://en.wikipedia.org/wiki/Double_Ratchet_Algorithm)
the KDF of which chains SHA3-256, Blake2s and SHA256.

The software is used in hardware configuration that provides strong 
endpoint security: Encryption and decryption are separated on two 
isolated computers. The split [TCB](https://en.wikipedia.org/wiki/Trusted_computing_base)
interacts with a third, networked computer through unidirectional [serial](https://en.wikipedia.org/wiki/RS-232)
interfaces. Direction of data flow is enforced with free hardware design
[data diodes](https://en.wikipedia.org/wiki/Unidirectional_network); Lack
of bidirectional channels to isolated computers prevents insertion of 
malware to the encrypting computer and exfiltration of keys and plaintexts
from the decrypting computer -- even with exploits against [zero-day vulnerabilities](https://en.wikipedia.org/wiki/Zero-day_(computing))
in software and operating systems of the TCB halves.

TFC supports multiple IM accounts per user to hide the network structure
of communicating parties, even during end-to-end encrypted group 
conversations.

TFC allows a group or two parties to defeat metadata about quantity and 
schedule of communication with trickle connection, where messages are 
inserted into a constant stream of encrypted noise traffic. Covert file 
transfer can take place in background during conversation over the 
trickle connection.

### How it works

![](https://cs.helsinki.fi/u/oottela/tfcwiki/tfc_overview2.jpg)

TFC uses three computers per endpoint. Alice enters her messages and 
commands to Transmitter program running on her transmitter computer (TxM), a 
TCB separated from network. The transmitter program encrypts and signs 
plaintext data and relays the ciphertext from TxM to her networked computer
(NH) trough a serial interface and a hardware data diode.

Messages and commands received to NH are relayed to IM client (Pidgin or
Finch), and to Alice's receiver computer (RxM) via another serial interface
and data diode. The Receiver program on Alice's RxM authenticates, decrypts
and processes the received messages and commands. 

The IM client sends the packet either directly or through Tor network to
IM server, that then forwards it directly (or again through Tor) to Bob.

IM client on Bob's NH forwards packet to nh.py plugin program, that then
forwards it to Bob's RxM (again through data diode enforced serial interface).
Bob's Receiver program on his RxM then authenticates, decrypts, and processes the packet.

When the Bob responds, he will type the message to his Transmitter computer and in the end,
Alice reads the message from her Receiver computer.


### Why keys can not be exfiltrated

1. Malware that exploits an unknown vulnerability in RxM can infiltrate
the system, but is unable to exfiltrate keys or plaintexts, as data
diode prevents all outbound traffic.

2. Malware can not infiltrate TxM as data diode prevents all inbound 
traffic. The only data input to TxM is the public key of contact, which 
is manually typed by the user.

3. The NH is assumed to be compromised: all sensitive data that passes
through NH is always encrypted and signed.

![](https://cs.helsinki.fi/u/oottela/tfcwiki/tfc_attacks2.jpg)

Optical repeater inside the [optocoupler](https://en.wikipedia.org/wiki/Opto-isolator)
of the data diode (below) enforces direction of data transmission with
the laws of physics.

<img src="https://cs.helsinki.fi/u/oottela/tfcwiki/bbdd.jpg" align="center" width="74%" height="74%"/>

### Supported Operating Systems

#### TxM and RxM
- *buntu 16.04
- Linux Mint 18.1 Serena

#### NH
- Tails 3.0
- *buntu 16.04
- Linux Mint 18.1 Serena

### More information
[Threat model](https://github.com/maqp/tfc/wiki/Threat-model)<br>
[FAQ](https://github.com/maqp/tfc/wiki/FAQ)<br>
[Security design](https://github.com/maqp/tfc/wiki/Security-design)<br>

Hardware<Br>
&nbsp;&nbsp;&nbsp;&nbsp;[Data diode (breadboard)](https://github.com/maqp/tfc/wiki/TTL-Data-Diode-(breadboard))<br>

Software<Br>
&nbsp;&nbsp;&nbsp;&nbsp;[Installation](https://github.com/maqp/tfc/wiki/Installation)<br>
&nbsp;&nbsp;&nbsp;&nbsp;[How to use](https://github.com/maqp/tfc/wiki/How-to-use)<br>

[Update Log](https://github.com/maqp/tfc/wiki/Update-Log)<br>
