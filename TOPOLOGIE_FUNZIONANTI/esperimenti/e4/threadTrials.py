# -*- coding: utf-8 -*-

from transaction import *
from message import *
from blockchain import *
from ledger import *
from node import *
import json
import time
import sys

 
BUFF = 1024
HOST = '127.0.0.1'# must be input parameter @TODO
PORT = 9999 # must be input parameter @TODO
MSGLEN = 4096

'''
def server_socket(host, port):
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind((host,port))
    serversock.listen(5)
    while 1:
        print 'waiting for connection...'
        clientsock, addr = serversock.accept()
        print '...connected from:', addr
        thread.start_new_thread(handler, (clientsock, addr))'''
 

bind_ip = '0.0.0.0'
bind_port = 9999


def prova_invio_messaggi():
    s = server('127.0.0.3', 10005, [])
    c = client('127.0.0.4', 10005, [s])
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    txset = transaction_set( [tx, tx2])
    mh = message_header(c.id(), c.signature(), 'm1', 0, message_type.transaction_set)
    mp = message_payload(txset)
    msg = message(mh, mp)
    c.send_all(msg)


def get_topo_from_json(filename):
    topo = []
    with open(filename, 'r') as file_topo:
        obj = json.load(file_topo)
        topo = obj["topology"]
    return topo

def build_txset_from_topo(topo):
    # First build dictionary having key = node_name, value = node
    nodes = {}
    for n in topo:
        node = topology_node(n["Name"], n["Type"])
        nodes[ n["Name"] ] = node
    # Then create transactions and finally pass them to the transaction_set
    transactions = []
    for n in topo:
        for to in n["Neighbors"]:
            tx = transaction (nodes[n["Name"]], nodes[to])
            transactions.append(tx)
    return transaction_set( transactions)


def prova_transazioni():
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    tx3 = transaction(r3, r5)
    unapproved = {tx:0, tx2:0}
    if tx3 in unapproved:
        print 'OK'
    assert tx2 == tx3

def prova_size_txset():
    c = client('127.0.0.12', 10000, [])
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    r6 = topology_node('r6', 'R')
    r7 = topology_node('r7', 'R')
    r8 = topology_node('r8', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    tx3 = transaction(r6, r5)
    tx4 = transaction(r2, r6)
    tx5 = transaction(r2, r7)
    tx6 = transaction(r2, r8)
    tx7 = transaction(r3, r6)
    tx8 = transaction(r3, r7)
    tx9 = transaction(r3, r8)
    tx10 = transaction(r7, r8)
    transactions = [tx]
    tx_set = transaction_set( transactions)
    header = message_header(c.id(), c.signature(), 'id', 0, message_type.transaction_set)
    payload = message_payload(tx_set)
    msg = message(header, payload)
    msg_bin = pickle.dumps(msg)
    print 'Size in bytes with one transaction: ' + str(sys.getsizeof(msg_bin))
    tx_set.add_transaction(tx2)
    payload = message_payload(tx_set)
    msg = message(header, payload)
    msg_bin = pickle.dumps(msg)
    print 'Size in bytes with 2 transaction: ' + str(sys.getsizeof(msg_bin))
    transactions = [tx3,tx4,tx5]
    for t in transactions:
        tx_set.add_transaction(t)
    payload = message_payload(tx_set)
    msg = message(header, payload)
    msg_bin = pickle.dumps(msg)
    print 'Size in bytes with 10 transaction: ' + str(sys.getsizeof(msg_bin))

def prova_registrazione():
    s = server('127.0.0.100', 10000, [])
    s2 = server('127.0.0.101', 10000, [])
    s3 = server('127.0.0.102', 10000, [])
    #c = client('127.0.0.12', 10000, [s.id()])
    #c.ask_registration()
    #time.sleep(3)
    #print c.stored_public_keys()
    #print s.observers


def prova_ledger():
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    txset = transaction_set([tx, tx2])
    l = full_ledger(0, txset)
    b = light_blockchain()
    b.add_ledger(l)
    b.add_ledger(l)
    b.add_ledger(l)
    ledgers = b.ledgers()
    print ledgers
    l2 = full_ledger(2, txset)
    l3 = full_ledger(3, txset)
    l4 = full_ledger(4, txset)
    l5 = full_ledger(5, txset)
    l6 = full_ledger(6, txset)
    l7 = full_ledger(7, txset)
    b = full_blockchain((7,3))
    b.add_ledger(l)
    b.add_ledger(l2)
    b.add_ledger(l3)
    b.add_ledger(l4)
    b.add_ledger(l5)
    b.add_ledger(l6)
    print 'size: ' + str(b.size())
    b.add_ledger(l7)
    print 'size after: ' + str(b.size())
    ledgers = b.ledgers()
    print ledgers

def prova_ledger_equality():
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    txset = transaction_set([tx, tx2])
    l = full_ledger(0, txset)
    tx3 = transaction(r2, r5)
    tx4 = transaction(r3, r5)
    txset2 = transaction_set([tx4, tx3])
    l2 = full_ledger(0, txset2)
    print 'Test: transaction_set sono uguali \n'
    assert txset == txset2
    print 'Test: ledger sono uguali \n'
    assert l == l2
    print 'Test: ledger sono diversi \n'
    l3 = full_ledger(1, txset2)
    assert l != l3

def prova_scambio_proposal():
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    trans = [tx, tx2]
    b = light_blockchain()
    s = server('127.0.0.100', 10000, 0.8, 5, 10, {}, {}, 10, 20, validators = [], unl =['127.0.0.101:10000'])
    s2 = server('127.0.0.101', 10000, 0.8, 5, 10, {}, {}, 10, 20, validators=[], unl=['127.0.0.100:10000'])
    c = client('127.0.0.102', '10000', [s, s2])
    c.ask_client_registration()
    c.send_transactions(trans)
    s.start()
    s2.start()
    time.sleep(10)
    s.stop()
    s2.stop()

def prova_id_txset():
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    txset = transaction_set([tx, tx2])
    r2b = topology_node('r2', 'R')
    r3b = topology_node('r3', 'R')
    r5b = topology_node('r5', 'R')
    txb = transaction(r2b, r5b)
    tx2b = transaction(r3b, r5b)
    txset2 = transaction_set([tx, tx2])
    return txset.id() == txset2.id()


def prova_stampa_proposal():
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')
    tx = transaction(r2, r5)
    tx2 = transaction(r3, r5)
    txset = transaction_set([tx, tx2])
    my_pos = proposal('0', 1, txset, '0')
    print str(my_pos.tx_set())


def prova_transazioni_delete():
    def configure_client(config_file):
        '''Uses the parameters defined in the configuration file to create a client and return it.'''
        with open(config_file, 'r') as file:
            obj = json.load(file)
            ip = obj["ip"]
            port = obj["port"]
            validators = []
            for v in obj["validators"]:
                v_id = v["ip"] + ":" + v["port"]
                validators.append(v_id)
            return client(ip, port, validators)
    c = configure_client("file_config_prova/client1_config.json")
    c.ask_client_registration()
    trans = []
    r3 = topology_node('r3', 'R')
    r4 = topology_node('r4', 'R')
    r2 = topology_node('R2', 'R')
    trans.append(transaction(r3,r4,False))
    trans.append(transaction(r4, r3, False))
    c.send_transactions(trans)

if __name__=='__main__':

    """sst = thread.start_new_thread(server_socket, (HOST, PORT))
    dict = {'a':'bb', 'aa':'alt'}
    pdict = pickle.dumps(dict)
    server = server_socket(HOST, PORT)
    server.start()
    client = client_socket(HOST, PORT)
    dict = {'hello1':1, 'hello2':2, 'hello3':3}
    pic_d = pickle.dumps(dict)
    client.send(pic_d)
    tx = transaction(1, 'r2', 'r5')
    print tx.__str__()
    #client.send('Hello2')
    #client.send('Hello3')
    print 'stuck' 
    """
    """ 
    s = server('127.0.0.1', 10000, [])
    c = client('127.0.0.2', 10000, [s])
    r2 = topology_node('r2', 'R')
    r3 = topology_node('r3', 'R')
    r5 = topology_node('r5', 'R')    
    tx = transaction ( r2, r5 )
    tx2 = transaction ( r3, r5 )    
    print 'id tx: ' + tx.id()
    print 'id tx2: ' + tx2.id()
    txset = transaction_set([tx ,tx2])
    c.send_all(tx)
    (bob_pub, bob_priv) = rsa.newkeys(512) #Public key has to be distributed to nodes..
    (bob_pub2, bob_priv2) = rsa.newkeys(512)
    print 'public key 1 : '
    print str(bob_pub)
    print 'public key 2 : '
    print bob_pub2
    message = 'hello Bob!'.encode('utf8')
    crypto = rsa.encrypt(message, bob_pub)
    print 'crypted message: ' + crypto
    message = rsa.decrypt(crypto, bob_priv)
    print(message.decode('utf8'))
    """
    #prova_invio_messaggi()
    #prova_transazioni()
    #prova_registrazione()
    #prova_size_txset()
    #prova_ledger()
    #prova_scambio_proposal()
    #print prova_id_txset()
    #prova_ledger_equality()
    #prova_stampa_proposal()
    prova_transazioni_delete()


    '''topo = get_topo_from_json("m_topo.json")
    txset = build_txset_from_topo(topo)
    for t in txset.transactions().values():
        print t'''
