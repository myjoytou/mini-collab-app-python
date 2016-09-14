import random
import sys
from twisted.web.static import File
from twisted.python import log
from twisted.web.server import Site
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource

from pymongo import errors
from pymongo import MongoClient


class DbHandler:
    def __init__(self):
        self.client = MongoClient('localhost', 27017, connect=False)
        self.db = self.client.sample
        self.collection = self.db.collab_document
        self.payload = ""

    def freshPayload(self, payload):
        if self.payload != payload:
            return True
        else:
            return False

    def get(self):
        log.msg('===================GET: getting called')
        res = self.db.collab_document.find_one({'username': 'test_user'})
        log.msg('the result is======================= {}'.format(res))
        return res

    def post(self, data):
        log.msg('=======================posting')
        log.msg('data is: {} '.format(data))
        resp = self.get();
        if resp['docs']:
            if not self.collection:
                self.collection = self.db.collab_document
            self.collection.update_one({'username': 'test_user'}, {'$set': {'docs': data}})
        else:
            if self.freshPayload(data):
                db_data = {'username': 'test_user', 'docs': data}
                if not self.collection:
                    self.collection = self.db.collab_document
                self.collection.insert_one(db_data)
        log.msg('==============From post the respose is: {}'.format(self.get()))

class SomeServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)
        res = self.factory.findPartner(self)
        response = self.factory.populateResult()
        if response:
            response = response.encode('utf-8')
            try:
                self.factory.initialCommunicate(self, response)
            except errors.OperationFailure:
                log.msg("Could not read from the DB!")


    def connectionLost(self, reason):
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        log.msg('the values are ==========={} == {}'.format(type(payload), isBinary))
        try:
            self.factory.writeBack(payload)
        except errors.OperationFailure:
            log.msg("Could not write to the db")
        # db_handler.post(payload)
        self.factory.communicate(self, payload, isBinary)

class ChatCommunicateFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(ChatCommunicateFactory, self).__init__(*args, **kwargs)
        self.clients = {}
        try:
            self.handler = DbHandler()
        except errors.WTimeoutError:
            log.msg("Could not connect to DB!")
        log.msg('==============================cmio')

    def writeBack(self, payload):
        self.handler.post(payload)

    def populateResult(self):
        response = self.handler.get()
        log.msg('==================Posting somehitn: {}'.format(response['docs']))
        if response['docs']:
            return response['docs']
        return False

    def register(self, client):
        self.clients[client.peer] = {"object": client, "partner": None}

    def unregister(self, client):
        self.clients.pop(client.peer)

    def findPartner(self, client):
        available_partners = [c for c in self.clients if c != client.peer
                              and not self.clients[c]["partner"]]
        if not available_partners:
            print("no partners for {} check in a moment".format(client.peer))
            return False
        else:
            partner_key = random.choice(available_partners)
            self.clients[partner_key]["partner"] = client
            self.clients[client.peer]["partner"] = self.clients[partner_key]["object"]
            return True

    def initialCommunicate(self, client, payload):
        client.sendMessage(payload)

    def communicate(self, client, payload, isBinary):
        c = self.clients[client.peer]
        c["object"].sendMessage(payload)
        c["partner"].sendMessage(payload)

if __name__ == "__main__":
    log.startLogging(sys.stdout)

    root = File(".")
    factory = ChatCommunicateFactory(u"ws://127.0.0.1:8080")
    factory.protocol = SomeServerProtocol
    resource = WebSocketResource(factory)

    root.putChild("sample", File('sample.html'))
    # root.putChild("style.css", File('style.css'))
    root.putChild(u"ws", resource)

    site = Site(root)
    reactor.listenTCP(8080, site)
    reactor.run()
