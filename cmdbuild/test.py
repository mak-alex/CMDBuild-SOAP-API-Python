#!/usr/bin/python

import logging
import datetime
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
from time import sleep
from suds.client import Client
from suds.wsse import Security, UsernameToken
from base64 import b64encode
try:
    from hashlib import sha1,md5
except:
    from sha import new as sha1
    from md5 import md5

# From https://gist.github.com/copitux/5029872
# Need to send a digest password to CMDBuild, plain text won't work
class UsernameDigestToken(UsernameToken):
    """
    Represents a basic I{UsernameToken} WS-Security token with password digest
    @ivar username: A username.
    @type username: str
    @ivar password: A password.
    @type password: str
    @ivar nonce: A set of bytes to prevent reply attacks.
    @type nonce: str
    @ivar created: The token created.
    @type created: L{datetime}

    @doc: http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0.pdf
    """

    def __init__(self, username=None, password=None):
        UsernameToken.__init__(self, username, password)
        self.setcreated()
        self.setnonce()

    def setnonce(self, text=None):
        """
        Set I{nonce} which is arbitraty set of bytes to prevent
        reply attacks.
        @param text: The nonce text value.
        Generated when I{None}.
        @type text: str

        @override: Nonce save binary string to build digest password
        """
        if text is None:
            s = []
            s.append(self.username)
            s.append(self.password)
            s.append(self.sysdate())
            m = md5()
            m.update(':'.join(s))
            self.raw_nonce = m.digest()
            self.nonce = b64encode(self.raw_nonce)
        else:
            self.nonce = text

    def xml(self):
        usernametoken = UsernameToken.xml(self)
        password = usernametoken.getChild('Password')
        nonce = usernametoken.getChild('Nonce')
        created = usernametoken.getChild('Created')
        password.set('Type', 'http://docs.oasis-open.org/wss/2004/01/'
                     'oasis-200401-wss-username-token-profile-1.0'
                     '#PasswordDigest')
        s = sha1()
        s.update(self.raw_nonce)
        s.update(created.getText())
        s.update(password.getText())
        password.setText(b64encode(s.digest()))
        nonce.set('EncodingType', 'http://docs.oasis-open.org/wss/2004'
                  '/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary')
        return usernametoken

if __name__ == '__main__':
    c = Client("http://10.244.244.128/cmdbuild/services/soap/Webservices?wsdl")

    # Authenticate to CMDBuild SOAP service
    s = Security()
    t = UsernameDigestToken('admin', '3$rFvCdE')

    s.tokens.append(t)
    c.set_options(wsse=s)
    c.set_options(retxml=True)

    # Query the list of buildings
    print c.service.getCardList("Hosts")
