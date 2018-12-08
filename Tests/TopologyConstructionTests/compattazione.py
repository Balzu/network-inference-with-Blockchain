import pdb, json, hashlib



class topology_node(object):
    """ Interface for a node of the topology. The type can be 'R', 'A', 'B', 'NC', 'H' or 'P'
    ('P' means arbitrary node added to fit the topology to a given pattern)"""
    def __init__(self, name, type):
        self._name = name
        self._type = type

    def __str__(self):
        return self._name+ ':' + self._type

    def __eq__(self, n2):
        if isinstance(n2, topology_node):
            return  self._name == n2.name() and self._type == n2.type()
        raise TypeError('The comparison must be done among two objects of class "topology_node" ')

    def __ne__(self, other):
        return not self.__eq__(other)

    def name(self):
        return self._name

    def type(self):
        return self._type

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

def get_topo_from_json(filename):
    topo = []
    with open(filename, 'r') as file_topo:
        obj = json.load(file_topo)
        topo = obj["topology"]
    return topo

def create_transactions_for_compacted_topo(topo):
    '''Creates a list of transactions for a compacted topology in which non responding routers are absent.'''
    # First build dictionary having key = node_name, value = (node, list of neighbors)
    nodes = {}
    for n in topo:
        node = topology_node(n["Name"], n["Type"])
        nodes[n["Name"]] = (node, n["Neighbors"][:])
    # Then create transactions and finally pass them to the transaction_set
    transactions = []
    for n in topo:
        if n["Type"] == "R":
            i = 0
            neighbors = n["Neighbors"][:]
            removed = [n["Name"]] if n["Name"] not in neighbors else []# To avoid the self-loop (if self-loop is not present)
            while i < len (neighbors):
                if nodes[neighbors[i]][0].type() != "R":
                    removed.append(neighbors[i])
                    neighbors = list(set(neighbors).union(set(nodes[neighbors[i]][1])))
                    neighbors = [v for v in neighbors if v not in removed]
                    i = 0
                else:
                    i += 1
            for dst in neighbors:
                transactions.append(transaction(nodes[n["Name"]][0], nodes[dst][0]))
    return transactions



topo = get_topo_from_json('prova_compattazione.json')
trans = create_transactions_for_compacted_topo(topo)
for t in trans:
    print t