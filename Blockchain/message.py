# coding=utf-8
class message(object):
    '''Wrapper class for the messages sent in the blockchain.
    It has a header of type 'message_header' and a payload of type 'message_payload'
    The content type matches the message 'type' attribute'''

    def __init__(self, header, payload):
        self.check_types(header, payload)
        self._header = header
        self._payload = payload


    def check_types(self, header, payload):
        if not isinstance(header, message_header):
            raise TypeError("header must be of type 'message_header'")
        if not isinstance(payload, message_payload):
            raise TypeError("payload must be of type 'message_payload'")
        #TODO rimane da controllare che attributo 'type' matchi il tipo di 'content'

    def sender(self):
        return self._header._sender

    def signature(self):
        return self._header._sign

    def id(self):
        return self._header._id

    def sequence_number(self):
        return self._header._seq

    def type(self):
        return self._header._type

    def content(self):
        return self._payload._content



class message_header(object):
    '''Header of a message.
    It specifies a sender with its signature.
    It has an ID and a sequence number, which is 0 if no other message is following to complete
    the current data transmission and 1 otherwise (payload could be too big to be sent
    in one shot). Finally, it contains the type of the payload'''

    def __init__(self, sender, sign, msg_id, seq, type):
        self._sender = sender
        self._sign = sign
        self._id = msg_id
        self._seq = seq
        self._type = type


class message_payload(object):
    '''Payload of a message'''
    def __init__(self, content):
        self._content = content



class message_type(object):
    '''Handmade enum for message type'''
    public_key = 1 #TODO ancora necessario?
    client_registration = 2
    observer_registration = 3
    client_deregistration = 4
    observer_deregistration = 5
    transaction = 6
    transaction_set = 7
    proposal = 8
    ledger = 9
    end = 10 #TODO necessario?


    ack_success = 20
    ack_failure = 21
