# coding=utf-8
import hashlib
from transaction import *

class ledger(object):
    '''Interface for the ledger'''
    def __init__(self, seq, txset, prev = None, next = None):
        self.__seq = seq
        self.__txset_id = txset.id()
        sha = hashlib.sha256()
        sha.update(str(seq))
        sha.update(str(txset.id()))
        self.__id = sha.digest()
        self.__previous = prev
        self.__next = next

    def __eq__(self, other):
        if isinstance(other, ledger):
            return self.__seq == other.sequence_number() and self.transaction_set().has_same_transactions(other.transaction_set())
            #self.transaction_set_id() == other.transaction_set_id() TODO era vecchia condizione, controlla
        raise TypeError('The comparison must be done among two objects of class "ledger" ')

    def __ne__(self, other):
        return not self.__eq__(other)

    def sequence_number(self):
        return self.__seq

    def id(self):
        return self.__id

    def transaction_set_id(self):
        pass

    #TODO check
    def transaction_set(self):
        pass

    def set_previous(self, ledger):
        self.__previous = ledger

    def get_previous(self):
        return self.__previous

    def set_next(self, ledger):
        self.__next = ledger

    def get_next(self):
        return self.__next

    def free_pointers(self):
        self.__previous = None
        self.__next = None

    def merge(self, other):
        pass

    def type(self):
        pass


class full_ledger(ledger):
    '''Full ledger, holding the whole transaction set'''

    def __init__(self, seq, txset, prev = None, next = None):
        super(full_ledger, self).__init__(seq, txset, prev, next)
        self.__txset = transaction_set(txset.transactions().values())
        self.__type = 'F'

    def transaction_set(self):
        return self.__txset

    def transaction_set_id(self):
        return self.__txset.id()

    def type(self):
        return self.__type

    def merge(self, other):
        if not isinstance(other, full_ledger):
            raise TypeError('The merge can happen only between two full_ledger objects')
        other_trans = other.transaction_set().transactions().values()
        for t in other_trans:
            self.transaction_set().add_transaction(t)
        return self #TODO check


class light_ledger(ledger):
    '''Light ledger, holding only the id of the transaction set.
       It carries the id of the initial transaction set. Successive modification to the transaction_set
       are not (automatically) reflected in the transaction set id'''

    def __init__(self, seq, txset, prev = None, next = None):
        super(light_ledger, self).__init__(seq, txset, prev, next)
        self.__type = 'L'

    def type(self):
        return self.__type

    def transaction_set_id(self):
        return self.__txset_id