# coding=utf-8
import hashlib


class transaction:
    """ A transaction is an edge made of two topology_nodes, with the indication
        of whether this edge has to be inserted or removed from the topology"""
    def __init__(self, _from, _to, insert=True):
        sha = hashlib.sha256()
        sha.update(str(_from))
        sha.update(str(_to))
        #sha.update(str(insert))
        self._id = sha.digest()  # The id does not keep into account if it is a transaction 'I' or 'D'
        self._from = _from
        self._to = _to
        self._type = 'I' if insert is True else 'D'

    def id(self):
        return self._id

    def src(self):
        return self._from

    def dst(self):
        return self._to

    def type(self):
        return self._type

    def __str__(self):
        try:
            return self._from.name() + ' -> ' + self._to.name()
        except AttributeError:
            if self._from is not None and self._to is None and self._type == 'D':
                return 'Delete Node ' + self._from.name()

    def copy(self):
        return transaction(self._from, self._to, True if self._type == 'I' else False)

    def __eq__(self, tx2):
        return self._id == tx2.id()

    def __hash__(self):
        return hash(str(self))


#TODO non è chiaro se l' ID al txset lo do' io ( magari incrementale, fatto da
# nome_nodo ( ch lo crea) + numero_transaction_set_creati ), oppure lo crei in base al contenuto
# ex: hash transazioni

class transaction_set:
    ''' Contains an ID and a dictionary st (key = transactionId, value = transaction).
    Two transaction_set have same ID if they contain same transactions'''
    def __init__(self,  transactions):
        sha = hashlib.sha256()
        self._transactions = {} # dict. st: key = tx_id, value = tx
        for tx in transactions:
            self._transactions[tx.id()] = tx.copy()
        for id in sorted(self._transactions.keys()):
            sha.update(id)
        self._id = sha.digest()

    def __eq__(self, other):
        if isinstance(other, transaction_set):
            return self._id == other.id()
        raise TypeError('The comparison must be done among two objects of class "transaction_set" ')

    def __ne__(self, other):
        return not self.__eq__(other)

    def id(self):
         return self._id

    def transactions(self):
       return self._transactions

    def add_transaction(self, tx):
        self._transactions[tx.id()] = tx
        # Every time a transaction is added the id must be updated, because it is used as fingerprint for the transactions
        sha = hashlib.sha256()
        for id in sorted(self._transactions.keys()):
            sha.update(id)
        self._id = sha.digest

    def remove_transaction(self, tx):
        try:
            del self._transactions[tx.id()]
            return True
        except KeyError:
            return False

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

    #TODO forse non più necessario
    def has_same_transactions(self, txset2):
        '''Two transaction_set are the same only if they have the same id, meaning that they carry the same
        transactions and those transactions were added in the same order. Here we only deal with content.'''
        transactions2 = txset2.transactions()
        if len(self._transactions) != len(transactions2):
            return False
        for tid in self.transactions():
            if tid not in transactions2:
                return False
        return True

    def __str__(self):
        stx = ''
        for tx in self._transactions.values():
            stx = stx + str(tx) + ', '
        return stx

    def copy(self):
        new_trans = {}
        transactions = self._transactions.values()
        for tx in transactions:
            new_trans[tx.id()] = tx.copy()
        return transaction_set(new_trans)

    def __contains__(self, trans):
        if not isinstance(trans, transaction):
            raise TypeError('The operator can be applied to objects of class "transaction" ')
        return trans.id() in self._transactions









