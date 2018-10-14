class proposal(object):
    '''Interface for the proposals sent by the blockchain nodes to update the ledger'''

    def __init__(self, nid, r, txset, lid, complete=True):
        self.__node_id = nid
        self.__round = r
        self.__tx_set = txset
        self.__ledger_id = lid
        self.__complete = complete  #If False, the current proposal is not yet completed. Some transactions have to be added

    def proposer(self):
        '''Returns the ID of the node that made this proposal'''
        return self.__node_id

    def round(self):
        return self.__round

    def tx_set(self):
        return self.__tx_set

    def tx_set_id(self):
        return self.__tx_set.id()

    def ledger_id(self):
        '''Returns the ID of the ledger to which this proposal is applied'''
        return self.__ledger_id

    def merge(self, other_prop, complete = True):
        '''Adds the transactions carried by the other proposal to the transaction_set of this proposal'''
        other_txset = other_prop.tx_set()
        other_trans = other_txset.transactions().values()
        for t in other_trans:
            self.__tx_set.add_transaction(t)
        if not self.complete(): # A complete transaction cannot be rendered uncomplete
            self.__complete = complete

    def complete(self):
        '''Returns True if the proposal is complete, i.e. don't have to wait for other transactions to be merged'''
        return self.__complete
