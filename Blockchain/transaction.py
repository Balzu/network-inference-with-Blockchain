# coding=utf-8
import hashlib


class transaction:
    """ A transaction is an edge made of two topology_nodes, with the indication
        of whether this edge has to be inserted or removed from the topology"""
    def __init__(self, _from, _to, insert=True):
        sha = hashlib.sha256()
        sha.update(str(_from))
        sha.update(str(_to))
        sha.update(str(insert))
        self._id = sha.digest()
        self._from = _from
        self._to = _to
        self._type = 'I' if insert is True else 'D'

    def id(self):
        return self._id

    def type(self):
        return self._type

    def __str__(self):
        return self._from.name() + ' -> ' + self._to.name()

    def copy(self):
        return transaction(self._from, self._to)

    def __eq__(self, tx2):
        return self._id == tx2.id()

    def __hash__(self):
        return hash(str(self))


#TODO non è chiaro se l' ID al txset lo do' io ( magari incrementale, fatto da
# nome_nodo ( ch lo crea) + numero_transaction_set_creati ), oppure lo crei in base al contenuto
# ex: hash transazioni
class transaction_set:
    ''' Contains an ID and a dictionary st (key = transactionId, value = transaction)'''
    def __init__(self, id, transactions):
        self._id = id
        self._transactions = {}
        for tx in transactions:            
            self._transactions[tx.id()] = tx.copy()

    def id(self):
         return self._id

    def transactions(self):
       return self._transactions

    def add_transaction(self, tx):
        self._transactions[tx.id()] = tx

    #TODO anche metodo che controlla presenza di una transazione in base al contenuto (e non all' ID)
    def exists (self, tx_id):
        '''Return True if the provided transaction ID is a key in the dictionary of transactions'''
        return tx_id in self._transactions

    # Returns the transaction of THIS set not in common with the provided transaction set (not the opposite!)
    def difference(self, txset2):
        diff = {}
        transactions2 = txset2.transactions()
        for tx_id in self._transactions.keys():
            if tx_id not in transactions2:
                diff [tx_id] = self._transactions[tx_id].copy()
        return diff

    def __str__(self):
        stx = ''
        for tx in self._transactions:
            stx + str(tx) 
        return stx









