# -*- coding: utf-8 -*-
from __future__ import division
import threading
import socket
import thread
import pickle
import rsa
import time
import pdb
from transaction import *
from message import *
from blockchain import *
from proposal import *

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
        #print 'Received: ' + ack

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
        #print 'Listening on {}:{}'.format(self.ip_addr, self.port)
        self.start_listening(server)

    def handle_client_connection(self, client_socket):
        msg = client_socket.recv(16384)
        #print 'Received {}'.format(pickle.loads(msg)) #TODO controlla dove mettere pickle
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
                #print 'Accepted connection from {}:{}'.format(address[0], address[1])
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
        msgs = self.create_txset_messages(transactions)
        if len(servers) == 0:
            self.send_all(msgs, list = True)
        else:
            for s in servers:
                self.send_to(msgs, s, list = True)

    def create_txset_messages(self, transactions):
        msgs = []
        num = len(transactions)
        while num > 50:
            tmp = transactions[0:50]
            header = message_header(self.id(), self.signature(), 'id', 1, message_type.transaction_set)
            payload = message_payload(transaction_set(tmp))
            msgs.append(message(header, payload))
            transactions = transactions[50:]
            num = len(transactions)
        header = message_header(self.id(), self.signature(), 'id', 0, message_type.transaction_set)
        payload = message_payload(transaction_set( transactions))
        msgs.append(message(header, payload))
        return msgs

    def send_all(self, msg, list = False, servers = []):
        """Send a message or a list of messages to all servers in the list.
        Default: If no list is provided, the messages are sent to the validators list."""
        threads = []
        dest = self.validators
        if len(servers) > 0:
            dest = servers
        for d in dest:
            t = threading.Thread(
                target=self.send,
                args=(msg, d, list,)
            )
            t.start()
            #thread.start_new_thread(self.send, (msg, v, list))

    def send_to(self, msg, node_id, list = False):
        """Send a message or a list of messages to the provided node"""
        t = threading.Thread(
            target=self.send,
            args=(msg, node_id, list,)
        )
        t.start()
        #thread.start_new_thread(self.send, (msg, node_id, list))

    def send(self, msg, node_id, list):
        '''Different handling done whether a single message is sent or a list of messages'''
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
        elif req_type == message_type.proposal:
            self.handle_proposal_response(response)
        # TODO elif conditions, one per case
        return

    def handle_registration(self, response):
        if response.type() == message_type.ack_success:
            id = response.sender()
            pub_key = response.content()
            self.add_public_key(id, pub_key)
            print 'Registration successfully carried out'

    #TODO contenuto può dirti num_tx_inserite / num_tx_totali
    def handle_txset_response(self, response):
        if response.type() == message_type.ack_success:
            ins = response.content()['inserted']
            tot = response.content()['total']
            print 'Successfully inserted ' + str(ins) + ' transactions out of ' + str(tot)
        else:
            print 'Transactions not successfully inserted'

    def handle_proposal_response(self, response):
        pass # A simple client does not manage proposals

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
        self.my_pos = None
        self.unl_pos = {} # Key: node_id, value : [proposals (not yet processed)]
        self.last_pos = {} # key: node_id, value: last_proposal. Also this node is included in this dictionary
        self.unl_ledgers = {} # key: node_id, value (received_all(boolean), ledger)
        for u in unl:
            self.unl_pos[u] = []
            self.last_pos[u] = None
            self.unl_ledgers[u] = (False, None)
        self.last_pos[self.id()] = None
        self.__blockchain = full_blockchain()

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

        print '\n................................................' \
              '\n\n\n            Open Phase               \n\n\n' \
              '................................................\n'

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
            self.current_tx.append(t)
        self.open = False



    def establish_phase(self):
        '''The Establish phase is the one in which this node tries to reach the consensus with the other nodes of
        the UNL on the transactions to include in the ledger. Proposals are exchanged until at least a quorum q
        of the nodes in the UNL agrees on the same transaction set.'''

        print '\n................................................' \
              '\n\n\n            Establish Phase               \n\n\n' \
              '................................................\n'

        def next_phase():
            elapsed = time.time() - start
            c1 = elapsed > self.ledger_min_consensus
            c2 = len(self.in_establish_phase) > (0.7 * len(self.unl)) or elapsed > self.ledger_max_consensus
            c3 = self.same_proposal() > (self.quorum * len(self.unl))
            return c1 and c2 and c3

        # Init
        self.establish = True
        start = time.time()
        r = [0] # Round of the proposal
        sleep_time = self.ledger_min_close / 2  # Avoid spin wait
        self.create_my_proposal(r)
        self.send_proposal(r)

        while not next_phase():
            time.sleep(sleep_time)
            if self.new_proposals():
                self.update_last_proposals()
                if self.update_my_proposal(time.time()- start, r):
                    self.send_proposal(r)

        # Phase finalization
        self.in_establish_phase = []
        self.reset_last_pos()
        self.establish = False

    def same_proposal(self):
        '''Returns the number of nodes in the unl that share the proposal of this node'''
        share = 0
        my_prop = self.last_pos[self.id()]
        for prop in self.last_pos.values():
            if prop!= None and prop.proposer() != self.id():
                if my_prop.tx_set() == prop.tx_set():
                    share += 1
        return share

    def new_proposals(self):
        num = 0
        for u in self.unl_pos:
            num += len(self.unl_pos[u])
        return num > 0

    def update_last_proposals(self):
        '''For each node the list of proposals not yet processed is kept (useful if a proposal is sent via
        multiple messages). This function simply takes the last unprocessed proposal from each node (if any)
        and sets it as last proposal.'''
        for n in self.unl_pos:
            if len(self.unl_pos[n]) != 0:
                max = 0
                last_prop = None
                for prop in self.unl_pos[n]:
                    if prop.round() > max:
                        max = prop.round()
                        last_prop = prop
                self.last_pos[last_prop.proposer()] = last_prop
                self.unl_pos[n] = []


    # Ogni mia transazione è testata contro l' ultima proposta di ciascun nodo della unl.
    # Se il numero di nodi in cui compare > quorum allora includi quella transazione nella mia proposta,
    # altrimenti la scarti
    def update_my_proposal(self, elapsed, r):
        '''Returns True if a new proposal was created, False otherwise.'''
        threshold = self.get_threshold_value(elapsed) * len(self.unl)
        votes = {} # key: transaction_id, value : (transaction, number of votes) (All the transactions are considered)
        for prop in self.last_pos.values():
            if prop != None and prop.proposer() != self.id(): #TODO al momento non considero le mie transazioni
                transactions = prop.tx_set().transactions().values()
                for tx in transactions:
                    if tx.id() not in votes:
                        votes[tx.id()] = (tx, 1)
                    else:
                        votes[tx.id()] = (tx, votes[tx.id()][1] + 1)
        self.current_tx = []
        for (t,v) in votes.values():
            if v > threshold:
                self.current_tx.append(t)
        return self.create_my_proposal(r)


    def get_threshold_value(self, elapsed):
        if elapsed < self.threshold_times['init']:
            return self.threshold_values['init']
        if elapsed < self.threshold_times['mid']:
            return self.threshold_values['mid']
        if elapsed < self.threshold_times['late']:
            return self.threshold_values['late']
        return self.threshold_values['stuck']

    def create_my_proposal(self, r):
        '''Creates a proposal from the list of current transactions and adds it to the dict of last positions
            if this proposal is different from the old one. Returns True if a new proposal different from the
            previous one was created, False otherwise.'''
        txset = transaction_set(self.current_tx)
        new_prop = proposal(self.id(), r[0], txset, self.__blockchain.current_ledger_id())
        if self.last_pos[self.id()] is None or new_prop.tx_set() != self.last_pos[self.id()].tx_set():
            self.last_pos[self.id()] = new_prop
            r[0] = r[0] + 1 # Updates the round
            return True
        return False

    def create_proposal_messages(self, transactions, r):
        msgs = []
        num = len(transactions)
        while num > 45:
            tmp = transactions[0:45]
            header = message_header(self.id(), self.signature(), 'id', 1, message_type.proposal)
            txset = transaction_set(tmp)
            payload = message_payload(proposal(self.id(), r[0], txset, self.__blockchain.current_ledger_id()))
            msgs.append(message(header, payload))
            transactions = transactions[45:]
            num = len(transactions)
        header = message_header(self.id(), self.signature(), 'id', 0, message_type.proposal)
        txset = transaction_set(transactions)
        payload = message_payload(proposal(self.id(), r[0], txset, self.__blockchain.current_ledger_id()))
        msgs.append(message(header, payload))
        return msgs

    def send_proposal(self, r):
        '''Sends a proposal to the observers. If the proposal carries too many transactions, fragment it.'''
        msgs = self.create_proposal_messages(self.current_tx, r)
        self.send_all(msgs, list=True, servers=self.observers)

    def reset_last_pos(self):
        self.my_pos = self.last_pos[self.id()] #TODO crea proposal nuova, con COPIA transazioni?
        for nid in self.last_pos:
            self.last_pos[nid] = None

    def accept_phase(self):
        print '\n................................................' \
              '\n\n\n             Accept Phase                  \n\n\n' \
              '................................................\n'
        self.accept = True

        consensus = self.validate_ledger()
        self.reset_unl_ledgers()
        self.update_unapproved_tx(consensus)
        #print '\n current_tx length ' + str(len(self.current_tx)) + '\n' #TODO remove line
        self.accept = False


    def validate_ledger(self):
        '''Applies the transactions to the old ledger to generate a new ledger, sends the new ledger to the observers
        and waits to receive the new ledger from the unl. If the new ledger of this node is equal to the ledger
        received from at least 'quorum' nodes of the unl then keep this ledger, otherwise discard this ledger and ask
        the full ledger to the unl.'''

        def wait_unl_ledgers():
            start = time.time()
            elapsed = time.time()
            while elapsed - start < self.ledger_max_consensus and not self.received_all_ledgers():
                time.sleep(self.ledger_max_consensus / 10)
                elapsed = time.time()

        def create_new_ledger():
            for t in self.my_pos.tx_set().transactions().values():  #TODO controlla che my_pos contenga l' ultima proposal
                if t.type() == 'I':
                    new_txset.add_transaction(t)
                else:
                    removed = new_txset.remove_transaction(t)
                    if not removed:
                        print 'The transaction ' + str(t) + ' was not inserted in previous ledger ' \
                              + str(last_ledger.sequence_number()) + '. Unable to remove it.'
            return full_ledger(last_ledger.sequence_number() + 1, new_txset) if last_ledger is not None \
                else full_ledger(1, new_txset) # Prev pointer added when ledger inserted in the blockchain

        def reached_consensus():
            ledgers = []
            for n in self.unl_ledgers:
                if self.unl_ledgers[n][1] is not None:
                    ledgers.append(self.unl_ledgers[n][1])
            # If this ledger is shared among the quorum, keep this
            share = 0
            for l in ledgers:
                if new_ledger == l:
                    share += 1
            if share > self.quorum * len(self.unl):
                print '\nReached consensus with my ledger\n'
                return True
            # Otherwise, if a quorum of nodes share the same ledger, use it as new ledger
            share = {}
            for l in ledgers:
                if l.id() not in share:
                    share[l] = 1
                else:
                    share[l] =  share[l] + 1
            for l in share:
                if share[l] > self.quorum * len(self.unl):
                    print '\nReached consensus with unl ledger\n'
                    return True
            print '\nNot reached consensus\n'
            return False

        #TODO check
        def check_seq_number():
            '''Returns True if the problem on reaching consensus is due to this node working on a different ledger
                (different sequence number) , False otherwise.'''
            ledgers = []
            for n in self.unl_ledgers:
                if self.unl_ledgers[n][1] is not None:
                    ledgers.append(self.unl_ledgers[n][1])
            threshold = len(self.unl) - len(self.unl) * self.quorum
            my_seq_num = 1 if last_ledger is None else last_ledger.sequence_number()
            diff = len(self.unl_ledgers)
            for l in ledgers: #ledgers could not contain all the ledgers of the nodes in the unl, so initialize diff with worst case result
                if l.sequence_number() == my_seq_num:
                    diff -= 1
            return diff > threshold # At most threshold differences are allowed to reach consensus

        last_ledger = self.__blockchain.current_ledger()
        new_txset = transaction_set(last_ledger.transaction_set().transactions().values()) if last_ledger is not None \
            else transaction_set([])
        new_ledger = create_new_ledger()
        self.send_ledger(new_txset.transactions().values(), new_ledger.sequence_number())
        wait_unl_ledgers()
        consensus = reached_consensus()
        if not consensus:
            if check_seq_number():
                seq_num = last_ledger.sequence_number() if last_ledger is not None else 1
                (consensus, new_ledger) = self.ask_ledgers(seq_num)
        if consensus:
            self.__blockchain.add_ledger(new_ledger)
        return consensus

    def received_all_ledgers(self):
        '''Returns True only if all the nodes in the UNL have sent entirely their ledger. Since a ledger may be
        fragmented to be sent in one message, the dict "unl_ledgers" carries a boolean for each node telling if
        that node has sent all its ledger to this node.'''
        for n in self.unl_ledgers:
            if self.unl_ledgers[n][0] == False:
                return False
        return True

    def send_ledger(self, transactions, seq):
        msgs = self.create_ledger_messages(transactions, seq)
        self.send_all(msgs, list=True, servers=self.observers)

    def create_ledger_messages(self, transactions, seq):
        msgs = []
        num = len(transactions)
        while num > 40:
            tmp = transactions[0:40]
            header = message_header(self.id(), self.signature(), 'id', 1, message_type.ledger)
            txset = transaction_set(tmp)
            payload = message_payload(full_ledger(seq, txset))
            msgs.append(message(header, payload))
            transactions = transactions[40:]
            num = len(transactions)
        header = message_header(self.id(), self.signature(), 'id', 0, message_type.ledger)
        txset = transaction_set(transactions)
        payload = message_payload(full_ledger(seq, txset))
        msgs.append(message(header, payload))
        return msgs

    #TODO: STOP finchè questo nodo non si è riaggiornato
    def ask_ledgers(self, my_seq_num):
        '''Checks which is the minimum sequence number between its own and the sequence numbers of the received ledgers.
            Once found the minimum, asks the unl to get all the ledgers starting from that seq_number up to the last.
            This way, this node returns updated wrt the network.'''
        return (False, None)


    def reset_unl_ledgers(self):
        for u in self.unl_ledgers:
            self.unl_ledgers[u] = (False, None)


    def update_unapproved_tx(self, consensus):
        '''Removes from unapproved_tx the transactions included in the validated ledger and ages the others'''
        if consensus:
            validated_trans_set = self.__blockchain.current_ledger().transaction_set()
            self.print_validated_tx(validated_trans_set) # TODO per debug. O lo rimuovi, o lo metti da qualche altra parte
            for t in self.unapproved_tx.keys():
                if t in validated_trans_set:
                    del self.unapproved_tx[t]
                else:
                    self.unapproved_tx[t] = self.unapproved_tx[t] + 1 # Age the transaction
                    if self.unapproved_tx[t] > 5: #TODO Hard coded, define in config file the maximum age
                        del self.unapproved_tx[t]
        else: # If consensus was not reach, age all the transactions
            for t in self.unapproved_tx.keys():
                self.unapproved_tx[t] = self.unapproved_tx[t] + 1  # Age the transaction
                if self.unapproved_tx[t] > 5:  # TODO Hard coded, define in config file the maximum age
                    del self.unapproved_tx[t]

    def print_validated_tx(self, txset):
        print '\n..............Ledger ' + str(self.__blockchain.current_ledger().sequence_number()) + ' ...................\n'
        for tx in txset.transactions().values():
            print tx
        print '\n....................................................\n'

    def add_node_to_unl(self, node_id):
        self.unl.append(node_id)
        self.unl_pos[node_id] = []

    def remove_node_from_unl(self, node_id):
        try:
            self.unl.remove(node_id)
            del self.unl_pos[node_id]
            return True
        except ValueError:
            return False

    # TODO usa lock per strutture dati condivise. Capisci dove possono nascere race conditions.
    # Usare > 1 lock può essere opportuno, altrimenti blocchi thread che lavorano su Strut. Dati diverse!
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
        elif type == message_type.ledger:
            ack_msg = self.handle_ledger(msg)
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
        #print 'Client ' + id + ' successfully registered'
        return self.create_success_ack_msg(self.public_key())

    def register_observer(self, msg):
        id = msg.sender()
        pub_key = msg.content()
        self.observers.append(id)
        self.add_public_key(id, pub_key)
        #print 'Observer ' + id + ' successfully registered'
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
        ins = 0
        tot = len(txset.transactions())
        for tx in txset.transactions().values():
            if tx not in self.unapproved_tx:
                self.unapproved_tx[tx] = 0
                ins += 1
        print 'Inserted ' + str(ins) + ' transactions out of ' + str(tot)
        return self.create_success_ack_msg({'inserted':ins, 'total' : tot})

    def handle_ledger(self, msg):
        print 'received ledger from ' + msg.sender()
        l = msg.content()
        sid = msg.sender()
        all = True if msg.sequence_number() == 0 else False
        if self.unl_ledgers[sid][1] is None:
            self.unl_ledgers[sid] = (all, l)
        else:
            self.unl_ledgers[sid] = (all, self.unl_ledgers[sid][1].merge(l))
        return self.create_success_ack_msg("Ledger correctly received")

    def handle_proposal(self, msg):
        print 'received proposal from ' + msg.sender()
        prop = msg.content()
        sid = msg.sender()
        self.update_establish_phase_list(sid)
        if len(self.unl_pos[sid]) == 0:
            self.unl_pos[sid].append(prop)
        else:
            self.manage_unempty_list(prop, sid)
        return self.create_success_ack_msg("Proposal correctly received")

    def update_establish_phase_list(self, id):
        for n in self.in_establish_phase:
            if n == id:
                return # Node already included in the list, nothing to do
        self.in_establish_phase.append(id) # Otherwise include the node in the list

    def manage_unempty_list(self, prop, sid):
        '''If the list is not empty, it means that some proposals is already arrived that was not managed yet.
        If it exists a proposal in the list with the same sequence number of the new one, it means that the proposal
        was fragmented when it was sent. In this case, we merge the two proposals into one. If instead the new proposal
        is not the newest, we don't insert it (if some transactions are lost, the next round of consensus will fix it)'''
        r = prop.round()
        max_r = 0
        greater = True
        for p in self.unl_pos[sid]:
            if p.round() == r:
                p.merge(prop)
                return
            if prop.round() < p.round():
                return
        self.unl_pos[sid].append(prop)

    def handle_proposal_response(self, response):
        if response.type() == message_type.ack_success:
            #print 'Proposal successfully received from node ' + response.sender()
            pass
        else:
            #print 'Proposal NOT successfully received from node ' + response.sender()
            pass

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
