# coding=utf-8
from ledger import *

class blockchain(object):

    def __init__(self, (capacity, num_keep) = (-1, -1)):
        self.__ledgers = None  # Linked list of ledgers
        self.__size = 0 # Actual number of ledgers
        self.check_capacity(capacity, num_keep)
        self.__capacity = capacity # Maximum number of ledgers. If 'capacity' == -1 no limits are set on the number of ledgers.
        self.__num_keep = num_keep # If the capacity is exceeded, only the last 'num_keep' ledgers are kept


    def check_capacity(self, capacity, num_keep):
        '''Only returns if correct values for the parameters are provided. (default deny)
           Some conditions are added to give more detailed info in case of errors.'''
        if capacity > 0 and num_keep > 0 and capacity > num_keep:
            return
        if capacity == -1 and num_keep == -1:
            return
        if (capacity == -1 and num_keep != -1) or (capacity != -1 and num_keep == -1):
            raise ValueError('If the number of ledgers is unbound, leave default values. Otherwise, specify '
                             'values greater than zero for both capacity and num_keep, with capacity > num_keep')
        if capacity > 0 and num_keep > 0 and capacity < num_keep:
            raise ValueError('The capacity must be greater than the number of deletions!')
        else:
            raise ValueError('Incorrect values of parameters')


    def ledgers(self):
        return self.__ledgers

    def add_ledger(self, l):
        pass

    def replace_ledgers(self, l):
        '''Replaces the old linked list of ledgers with the new one provided.
        Usually used to change the head of the linked list.'''
        self.__ledgers = l

    def size(self):
        return self.__size

    def capacity(self):
        return self.__capacity

    def set_size(self, val):
        self.__size = val

    def discard_old_ledgers(self):
        iter = 0
        pnt = self.__ledgers
        while iter < self.__num_keep:
            pnt = pnt.get_previous()
            iter += 1
        pnt.get_next().set_previous(None) # This deletion must be done by hand
        while pnt is not None:
            tmp = pnt
            pnt = pnt.get_previous()
            tmp.free_pointers()
            del tmp
        self.__size = self.__num_keep

    def current_ledger(self):
        return self.__ledgers

    def current_ledger_id(self):
        return self.__ledgers.id() if self.__ledgers is not None else 0 # If no ledgers are present, return default value 0

class light_blockchain(blockchain):

    def __init__(self, (capacity, num_keep) = (-1, -1)):
        super(light_blockchain, self).__init__((capacity, num_keep))

    def add_ledger(self, new):
        '''Adds a ledger to the blockchain. Only the last ledger is a full_ledger. All the previous ledgers are
        light_ledger. The modification to the the ledger list involves the three last ledgers (penultimate -> last -> new)'''
        last = self.ledgers()
        if last is None:
            # Only add the new (full) ledger
            #last = new
            self.replace_ledgers(new)
        elif last.get_previous() is None:
            light_last = light_ledger(last.sequence_number(), last.transaction_set(), next = new)
            del last
            new.set_previous(light_last)
            #last = new
            self.replace_ledgers(new)
        else:
            penultimate = last.get_previous()
            light_last = light_ledger(last.sequence_number(), last.transaction_set(), prev=penultimate, next=new)
            del last
            penultimate.set_next(light_last)
            new.set_previous(light_last)
            #last = next
            self.replace_ledgers(new)
        self.set_size(self.size() + 1)
        if self.capacity() != -1:
            if self.size() >= self.capacity():
                self.discard_old_ledgers()


class full_blockchain(blockchain):

    def __init__(self, (capacity, num_keep) = (-1, -1)):
        super(full_blockchain, self).__init__((capacity, num_keep))

    def add_ledger(self, new):
        '''Adds a ledger to the blockchain. All the ledgers in the linked list are full_ledger.'''
        last = self.ledgers()
        if last is None:
            self.replace_ledgers(new)
        else:
            last.set_next(new)
            new.set_previous(last)
            self.replace_ledgers(new)
        self.set_size(self.size() + 1)
        if self.capacity() != -1:
            if self.size() >= self.capacity():
                self.discard_old_ledgers()



