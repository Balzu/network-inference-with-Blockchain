# network-inference-with-Blockchain

### TODO

Exception in thread Thread-499:
Traceback (most recent call last):
  File "/usr/lib/python2.7/threading.py", line 810, in __bootstrap_inner
    self.run()
  File "/usr/lib/python2.7/threading.py", line 763, in run
    self.__target(*self.__args, **self.__kwargs)
  File "/home/mininet/guest_share/network-inference-with-BlockchainNEW/Blockchain/node.py", line 255, in send
    ack = sender.recv(1024)
error: [Errno 104] Connection reset by peer

## Nota
Ogni volta che sniffi pacchetto ip da sensore riporti il suo fail count a 0. E' controllo in più, oltre al PING ciclico.
Quando elimini un host perchè non risponde a ping, non riammeterlo più! ( serve struttura dati)
