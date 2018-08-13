# -*- coding: utf-8 -*-
from __future__ import division
import threading
import socket
import thread
import pickle
import rsa
import time
from message import *

#TODO client_socket forse non serve più
class client_socket:
    def __init__(self, ip_addr, port):
        self.ip_addr = ip_addr
        self.port = port

    def send(self, msg):
        sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sender.connect((self.ip_addr, self.port))
        sender.sendall(msg)
        ack = sender.recv(1024)
        sender.close()
        print 'Received: ' + ack

class server_socket(threading.Thread):
    def __init__(self, ip_addr, port, server):
        super(server_socket, self).__init__()
        self.ip_addr = ip_addr
        self.port = port
        self.server = server # Used in callbacks
        self.end = False

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(5.0)
        server.bind((self.ip_addr, self.port))
        server.listen(5)  # max backlog of connections
        print 'Listening on {}:{}'.format(self.ip_addr, self.port)
        self.start_listening(server)

    def handle_client_connection(self, client_socket):
        msg = client_socket.recv(16384)
        print 'Received {}'.format(pickle.loads(msg)) #TODO controlla dove mettere pickle
        msg = pickle.loads(msg)
        ack_msg = self.server.handle_message(msg)
        ack_msg = pickle.dumps(ack_msg)
        client_socket.send(ack_msg) # ack message is no longer a string, but a 'message'
        client_socket.close()

    def stop(self):
        self.end = True

    '''TODO Aggiungi condizione booleana 'end', che viene settata dal main() quando il programma deve terminare
     (può essere messaggio particolare per socket), un TIMEOUT sulla wait che dopo un po' di tempo senza connessioni
     lo riporta a testare la condizione ( che invece di 'while TRUE' diventa 'while not end') '''
    def start_listening(self, server):
        while not self.end:
            try:
                client_sock, address = server.accept()
                print 'Accepted connection from {}:{}'.format(address[0], address[1])
                client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_sock,)
                )
                client_handler.start()
            except socket.timeout:
                pass



class topology_node(object):
    """ Interface for a node of the topology. The type can be 'R', 'A', 'B', 'NC', 'H' """
    def __init__(self, name, type):
        self._name = name
        self._type = type

    def __str__(self):
        return self._name+ ' : ' + self._type

    def name(self):
        return self._name

class node(object):
    """Interface for a node of the blockchain network"""
    def __init__(self, ip_addr, port):
        self._id = str(ip_addr) + ':' + str(port)   #TODO per ora l' id è praticamente il socket. Potrebbe essere ricavato da chiave pubblica
        self._ip = ip_addr
        self._port = port
        (self._pubkey, self._privkey) = rsa.newkeys(512)
        self._public_keys = {}
        self._end = False

    def ip(self):
        return self._ip

    def port(self):
        return self._port

    def id(self):
        return self._id

    def public_key(self):
        '''Return the public key of this node'''
        return self._pubkey

    def add_public_key(self, id, key):
        '''Adds the pair (node_id, public_key) to the dictionary of public keys'''
        self._public_keys[id] = key

    def remove_pub_key(self, id):
        del self._public_keys[id]

    def stored_public_keys(self):
        return self._public_keys

    def signature(self):
        '''Returns the cryptographic signature of the id of this node.'''
        return rsa.sign(self._id, self._privkey, 'SHA-256')

    def verify_signature(self, msg, type):
        '''The verification of the signature is done by looking at the stored public keys.
        In case the received message is a registration request, the key is taken from the message itself.'''
        try:
            id = msg.sender()
            sign = msg.signature()
            pub_key = msg.content() if type == message_type.client_registration or type == message_type.observer_registration \
                else self.stored_public_keys()[id]
            rsa.verify(id, sign, pub_key) # If verification fails, raises an error
            return True
        except KeyError: #TODO creare due messaggi di errore con testo diverso a seconda dell' eccezione? Credo meglio di no
            return False
        except rsa.VerificationError:
            return False

    def start(self):
        pass

    def end(self):
        return self._end

    def finalize(self):
        pass

    def stop(self):
        '''Stops the execution of the node'''
        self._end = True
        self.finalize()


class client(node):
    """Client node, that joins the network only to send transactions to be included in the ledger.
       It has a list of server nodes which should validate its transactions"""

    def __init__(self, ip_addr, port, validators = []):
        super(client, self).__init__( ip_addr, port)
        self.validators = validators #TODO must be a list of type node

    def add_validator(self, node_id):
        self.validators.append(node_id)

    def remove_validator(self, node_id):
        try:
            self.validators.remove(node_id)
            return True
        except ValueError:
            return False

    #TODO devi gestire in qualche modo l' esito della richiesta di registrazione, per esempio
    # usando lista 'Observed' che tiene conto dei nodi effettivamente osservati
    def ask_client_registration(self, servers = []):
        '''Asks the servers in the provided list to register this node as client
        (store its public key).
        If an empty list is provided, the validators list is used instead'''
        msg = self.create_client_registration_msg()
        if len(servers) == 0:
            self.send_all(msg)
        else:
            for s in servers:
                self.send_to(msg, s)

    def create_client_registration_msg(self):
        header = message_header(self.id(), self.signature(), 'id', 0, message_type.client_registration)
        payload = message_payload(self.public_key())
        return message(header, payload)

    def send_transactions(self, transactions, servers=[]):
        '''Sends the transactions to the provided list of servers or to the validators if no list is provided.
        The maximum number of transactions that can be sent in a single message is 50.'''
        msgs = self.create_txset_message(transactions)
        if len(servers) == 0:
            self.send_all(msgs, list = True)
        else:
            for s in servers:
                self.send_to(msgs, s, list = True)

    def create_txset_messages(transactions):
        msgs = []
        num = len(transactions)
        while num > 50:
            tmp = transactions[0:50]
            header = message_header(self.id(), self.signature(), 'id', 1, message_type.transaction_set)
            payload = message_payload(transaction_set('id', tmp))
            msgs.append(message(header, payload))
            transactions = transactions[50:]
            num = len(transactions)
        header = message_header(self.id(), self.signature(), 'id', 0, message_type.transaction_set)
        payload = message_payload(transaction_set('id', transactions))
        msgs.append(message(header, payload))
        return msgs


    def send_all(self, msg, list = False):
        """Send a message or a list of messages to all servers in the validator list"""
        for v in self.validators:
             thread.start_new_thread(self.send, (msg, v, list))

    def send_to(self, msg, node_id, list = False):
        """Send a message or a list of messages to the provided node"""
        thread.start_new_thread(self.send, (msg, node_id, list))

    def send(self, msg, node_id, list):
        '''Different handling done wheter a single message is sent or a list of messages'''
        ip_addr = node_id.split(':')[0]
        port = int(node_id.split(':')[1])
        sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sender.connect((ip_addr, port))
        if not list:
            pmsg = pickle.dumps(msg)
            sender.sendall(pmsg) # No need for lock on msg, it is just read
            ack = sender.recv(1024)
            ack = pickle.loads(ack)
            self.handle_response(msg.type(), ack)
            sender.close()
        else:
            for m in msg:
                pmsg = pickle.dumps(m)
                sender.sendall(pmsg) # No need for lock on msg, it is just read
                ack = sender.recv(1024)
                ack = pickle.loads(ack)
                self.handle_response(m.type(), ack)
            sender.close()


    #TODO: aggiungi un handler per ogni possibile tipo di messaggio
    def handle_response(self, req_type, response):
        '''Handles the response received by the server. A different handling is done
        based on the type of the request'''
        if not self.verify_signature(response, req_type):
            print 'Client ' + self.id() + 'couldn\'t verify the identity of ' + response.sender()
            return
        if req_type == message_type.client_registration or req_type == message_type.observer_registration:
            self.handle_registration(response)
        elif req_type == message_type.transaction_set:
            self.handle_txset_response(response)
        # TODO elif conditions, one per case
        return

    def handle_registration(self, response):
        if response.type() == message_type.ack_success:
            id = response.sender()
            pub_key = response.content()
            self.add_public_key(id, pub_key)
            print 'Registration successfully carried out'

    def handle_txset_response(self, response):
        if response.type() == message_type.ack_success:
            print 'Registration successfully carried out'
        else:
            print 'Registration not successfully carried out'

    #TODO send de-registration message to all validators?
    def finalize(self):
        pass


class server(client):
    """A server node of the blockchain network, running the consensus algorithm.
       It is also a client, because it both listens for incoming connections, and starts new connections."""
    def __init__(self, ip_addr, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, validators = [], unl = []):
        super(server, self).__init__(ip_addr, port, validators)
        self.observers = [] # Observers are the nodes that inserted this node in their UNL plus the clients of this node
        self.unl = unl
        self.unapproved_tx = {} # Dict st key=transaction, value = number of times transaction rejected by consensus
        self.current_tx = [] #Transactions that are being validated in the current consensus round
        self.in_establish_phase = [] # Number of nodes of UNL that moved on to the establish phase
        self.ssocket = server_socket(ip_addr, port, self)
        self.ssocket.start()
        self.quorum = q
        self.ledger_min_close = lmc
        self.ledger_max_close = lmcl
        self.threshold_values = tval
        self.threshold_times = ttimes
        self.ledger_min_consensus = lminc
        self.ledger_max_consensus = lmaxc
        self.open = True
        self.establish = False
        self.accept = False

    def start(self):
        '''Start this server in a separate thread of execution'''
        thread.start_new_thread(self.run, ())

    def run(self):
        while not self.end():
            self.open_phase()
            self.establish_phase()
            self.accept_phase()
        print 'end'
        #self.stop()

    def open_phase(self):
        '''In the open phase, the node simply collects transactions.
        When one of the three conditions defined in "next_phase()" holds,
        the node passes to the "Establish" phase.'''
        def next_phase():
            elapsed = time.time() - start
            c1 = bool(self.unapproved_tx) and elapsed > self.ledger_min_close #Dict evaluates to True if it is non empty
            c2 = elapsed > self.ledger_max_close
            c3 = len(self.in_establish_phase) > (0.5 * len(self.unl))
            return (c1 or c2 or c3)

        self.open = True
        start = time.time()
        sleep_time = self.ledger_min_close / 3  # Avoid spin wait
        while not next_phase():
            time.sleep(sleep_time)
        # Only the transactions already received will be part of the current round of consensus
        for t in self.unapproved_tx:
            self.current_tx.append(self.unapproved_tx[t])
        self.open = False


    # TODO
    def establish_phase(self):
        pass

     # TODO rimuovi transazioni approvate da 'unapproved_tx', incrementa il numero a quelle non approvate ( scarta
     # quelle troppo vecchie), e svuota 'current_tx'
    def accept_phase(self):
        pass

    def add_node_to_unl(self, node_id):
        self.unl.append(node_id)

    def remove_node_from_unl(self, node_id):
        try:
            self.unl.remove(node_id)
            return True
        except ValueError:
            return False

    def handle_message(self, msg):
        ack_msg = None
        type = msg.type()
        if not self.verify_signature(msg, type):
            return self.create_unsuccess_ack_msg("Unrecognized signature")
        if type == message_type.client_registration:
            ack_msg = self.register_client(msg)
        elif type == message_type.observer_registration:
            ack_msg = self.register_observer(msg)
        # transaction and transaction_set can only be received by a client
        elif type == message_type.transaction:
            ack_msg = self.add_transaction(msg)
        elif type == message_type.transaction_set:
            ack_msg = self.add_transactions(msg)
        elif type == message_type.proposal:
            ack_msg = self.handle_proposal(msg)
        #TODO puoi inviare richiesta di stop dalla rete?
        #elif type == message_type.end:
        #    ack_msg == self.stop(msg)
        else:
            ack_msg = self.create_unsuccess_ack_msg("Unrecognized type of the request message")
        return ack_msg

    def create_unsuccess_ack_msg(self, text, msg_id = "id"):
        header = message_header(self.id(), self.signature(), msg_id, 0, message_type.ack_failure ) #TODO per id usa un contatore di messaggi?
        payload = message_payload(text)
        ack_msg = message(header, payload)
        return ack_msg

    def create_success_ack_msg(self, content, type = message_type.ack_success, msg_id="id", seq_num = 0 ):
        header = message_header(self.id(), self.signature(), msg_id, seq_num, type ) #TODO per id usa un contatore di messaggi?
        payload = message_payload(content)
        ack_msg = message(header, payload)
        return ack_msg

    def register_client(self, msg):
        id = msg.sender()
        pub_key = msg.content()
        self.add_public_key(id, pub_key)
        print 'Client ' + id + ' successfully registered'
        return self.create_success_ack_msg(self.public_key())

    def register_observer(self, msg):
        id = msg.sender()
        pub_key = msg.content()
        self.observers.append(id)
        self.add_public_key(id, pub_key)
        print 'Observer ' + id + ' successfully registered'
        return self.create_success_ack_msg(self.public_key())

    def deregister_observer_with_msg(self, msg):
        '''An observer can be deregistered both if that node asks it with a message
           or if this node takes independently this decision (maybe it is a fraudolent node)'''
        id = msg.id()
        try:
            self.observers.remove(id)
            self.remove_pub_key(id)
            return self.create_success_ack_msg("Deregistration successfully carried out")
        except ValueError:
            return self.create_unsuccess_ack_msg("Node has not been registered yet. Unable to remove it.")

    def deregister_observer(self, id):
        try:
            self.observers.remove(id)
            self.remove_pub_key(id)
            return True
        except ValueError:
            return False

    def deregister_client(self, id):
        try:
            self.remove_pub_key(id)
            return True
        except ValueError:
            return False


    def add_transaction(self, msg):
        tx = msg.content()
        if tx not in self.unapproved_tx:
            self.unapproved_tx[tx] = 0
            return self.create_success_ack_msg("Transaction successfully inserted")
        else:
            return self.create_unsuccess_ack_msg("Transaction already received")

    def add_transactions(self, msg):
        txset = msg.content()
        for tx in txset.transactions():
            if tx not in self.unapproved_tx:
                self.unapproved_tx[tx] = 0
        return self.create_success_ack_msg("Transactions inserted")

    # TODO implementa quando hai deciso un po' il protocollo
    def handle_proposal(self, msg):
        return self.create_success_ack_msg("TODO")

    def ask_observer_registration(self, servers = []):
        '''Asks the servers in the provided list to register this node as observer.
        If an empty list is provided, the unl list is used instead'''
        msg = self.create_observer_registration_msg()
        if len(servers) == 0:
            servers = self.unl
        for s in servers:
                self.send_to(msg, s)

    def create_observer_registration_msg(self):
        header = message_header(self.id(), self.signature(), 'id', 0, message_type.observer_registration)
        payload = message_payload(self.public_key())
        return message(header, payload)

    # TODO send de-registration message to unl, end message to observers, and stop sockets?
    def finalize(self):
        self.ssocket.stop()
