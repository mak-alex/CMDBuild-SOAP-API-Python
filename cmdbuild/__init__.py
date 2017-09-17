# -*- coding: utf-8 -*-
import re
import json
import collections
import requests
import datetime

from lxml import etree
from lxml.etree import Element, SubElement, QName, tostring, fromstring

from base64 import b64encode
try:
    from hashlib import sha1,md5
except:
    from sha import new as sha1
    from md5 import md5

ns0_NAMESPACE = 'http://soap.services.cmdbuild.org'
ns0 = "{%s}" % ns0_NAMESPACE
ns1_NAMESPACE = 'http://schemas.xmlsoap.org/soap/envelope/'
ns1 = "{%s}" % ns1_NAMESPACE
SOAPENV = "{%s}" % ns1_NAMESPACE
xsi_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
xsi = "{%s}" % xsi_NAMESPACE
oasisopen = 'http://docs.oasis-open.org/wss/2004/01/'
EncodingType_NAMESPACE = oasisopen + '/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary' 
EncodingType = "{%s}" % EncodingType_NAMESPACE
wsse_NAMESPACE = oasisopen + "oasis-200401-wss-wssecurity-secext-1.0.xsd"
wsse = "{%s}" % wsse_NAMESPACE
wsu_NAMESPACE = oasisopen + "oasis-200401-wss-wssecurity-utility-1.0.xsd"
wsu = "{%s}" % wsu_NAMESPACE
PassText = oasisopen + "oasis-200401-wss-username-token-profile-1.0#PasswordText"
PassDigest = oasisopen + "oasis-200401-wss-username-token-profile-1.0#PasswordDigest"
NSMAP = {
    'ns0': ns0_NAMESPACE, 'ns1': ns1_NAMESPACE,
    'xsi': xsi_NAMESPACE, 'wsse': wsse_NAMESPACE,
    'wsu': wsu_NAMESPACE, 'SOAP-ENV': ns1_NAMESPACE,
}

def xml2dict(el):
    outtab = {}
    outtab['Id'] = {}
    def cards(el):
        for child in el:
            id = el.find(ns0+'id').text
            tag = child.tag.split('}')[1] if '}' in child.tag else child.tag
            if tag == 'attributeList':
                key = child.find(ns0+'name').text
                code = child.find(ns0+'code')
                value = child.find(ns0+'value').text
                if code is not None: code = code.text
                if not id in outtab['Id']: outtab['Id'][id] = {}
                if not code and value:
                    outtab['Id'][id][key] = value
                elif value:
                    outtab['Id'][id][key] = {'value': value, 'code': code}
        return outtab

    def fault(el):
        for child in el:
            key = child.tag.split('}')[1] if '}' in child.tag else child.tag
            value = child.text
            outtab['Id'][key] = value

    def id(el):
        key = el.tag.split('}')[1] if '}' in el.tag else el.tag
        value = el.text
        outtab['Id'][key] = value


    for i in el.findall(ns0+'cards'):
        if i.tag.split('}')[1] if '}' in i.tag else i.tag == 'cards': cards(i)

    if len(outtab['Id']) == 0:
        fault(el)

    if len(outtab['Id']) == 0:
        id(el)

    return outtab

class CMDBuild:
    def __init__(self, username=None, password=None, url=None, use_digest=False, nonce=None, created=None, verbose=False):
        self.url = url
        self.username = username
        self.password = password
        self.verbose = verbose
        self.Envelope = None
        self.Body = None
        self.use_digest = use_digest
        if use_digest:
            self.nonce = nonce
            self.setnonce()
            self.created = created
        self.response = None

    def pretty_print(self, resp=None):
        if not self.response:
            self.response = resp
        if isinstance(self.response, dict):
            print(json.dumps(self.response, encoding='UTF-8', indent=2))
        else:
            print(tostring(self.response, pretty_print=True))

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
            s.append(datetime.datetime.now().isoformat())
            m = md5()
            m.update(':'.join(s.encode('utf-8')))
            self.raw_nonce = m.digest()
            self.nonce = b64encode(self.raw_nonce)
        else:
            self.nonce = text

    def get_timestamp(self, timestamp=None):
        timestamp = timestamp or datetime.datetime.utcnow()
        return timestamp.isoformat() + 'Z'

    def __create_header__(self,):
        self.Envelope = etree.Element(SOAPENV + "Envelope", nsmap=NSMAP)
        Header = SubElement(self.Envelope, SOAPENV + 'Header', nsmap=NSMAP)
        Security  = SubElement(Header, wsse + 'Security', nsmap=NSMAP)
        UsernameToken = SubElement(Security, wsse + 'UsernameToken', nsmap=NSMAP)
        Username = SubElement(UsernameToken, wsse + 'Username', nsmap=NSMAP)
        Username.text = self.username
        Password = SubElement(UsernameToken, wsse + 'Password', nsmap=NSMAP)
        if not self.use_digest:
            Password.attrib['Type'] = PassText
        else:
            Password.attrib['Type'] = PassDigest
            created = SubElement(UsernameToken,  wsu + 'Created', nsmap=NSMAP)
            created.text = self.get_timestamp(self.created)
            nonce = SubElement(UsernameToken,  wsse + 'Nonce', nsmap=NSMAP)
            nonce.attrib['EncodingType'] = EncodingType_NAMESPACE
            nonce.text = self.nonce
            s = sha1()
            s.update(self.raw_nonce)
            s.update(self.get_timestamp(self.created))
            s.update(self.password)
            self.password = b64encode(s.digest())
        Password.text = self.password

        self.Body = SubElement(self.Envelope, ns1 + 'Body', nsmap=NSMAP)

    def getCard(self, classname, cardid, attributes=None):
        self.__create_header__()
        getCard = SubElement(self.Body, ns0 + 'getCard', nsmap=NSMAP)
        SubElement(getCard, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(getCard, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        if attributes:
            if isinstance(attributes, list):
                for attr in attributes:
                    attribute = SubElement(getCard, ns0 + 'attributeList')
                    SubElement(attribute, ns0 + 'name', nsmap=NSMAP).text = attr

        self.response = self.__request__()

    def deleteCard(self, classname, cardid):
        self.__create_header__()
        deleteCard = SubElement(self.Body, ns0 + 'deleteCard', nsmap=NSMAP)
        SubElement(deleteCard, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(deleteCard, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        self.response = self.__request__()

    def createCard(self, classname, attributes=None, metadata=None):
        self.__create_header__()
        createCard = SubElement(self.Body, ns0 + 'createCard', nsmap=NSMAP)
        cardType = SubElement(createCard, ns0 + 'cardType', nsmap=NSMAP)
        SubElement(cardType, ns0 + 'className', nsmap=NSMAP).text = classname

        if attributes:
            if isinstance(attributes, dict):
                for k, v in attributes.items():
                    attributeList = SubElement(cardType, ns0 + 'attributeList', nsmap=NSMAP)
                    SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                    SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)
            elif isinstance(attributes, list):
                for attr in attributes:
                    for k, v in attr.items():
                        attributeList = SubElement(cardType, ns0 + 'attributeList', nsmap=NSMAP)
                        SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                        SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)
            else:
                print('unknown type attributes: {}'.format(type(attributes)))
                sys.exit(1)

        if metadata:
            for k, v in metadata.items():
                metadata = SubElement(cardType, ns0 + 'metadata', nsmap=NSMAP)
                SubElement(metadata, ns0 + str(k), nsmap=NSMAP).text = str(v)

        self.response = self.__request__()

    def updateCard(self, classname, cardid, attributes=None, metadata=None):
        self.__create_header__()
        updateCard = SubElement(self.Body, ns0 + 'updateCard', nsmap=NSMAP)
        card = SubElement(updateCard, ns0 + 'card', nsmap=NSMAP)
        SubElement(card, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(card, ns0 + 'id', nsmap=NSMAP).text = str(cardid)

        if attributes:
            attributeList = SubElement(card, ns0 + 'attributeList', nsmap=NSMAP)
            for k, v in attributes.items():
                SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)

        if metadata:
            metadata = SubElement(card, ns0 + 'metadata', nsmap=NSMAP)
            for k, v in metadata.items():
                SubElement(metadata, ns0 + str(k), nsmap=NSMAP).text = str(v)

        self.response = self.__request__()

    def getCardList(self, classname, attributes=None, _filter=None,
                    filter_sq_operator=None, order_type=None,
                    limit=None, offset=None, full_text_query=None,
                    cql_query=False, cql_query_params=None):
        self.__create_header__()
        getCardList = SubElement(self.Body, ns0 + 'getCardList', nsmap=NSMAP)
        SubElement(getCardList, ns0 + 'className', nsmap=NSMAP).text = classname
        if attributes:
            if isinstance(attributes, list):
                for attr in attributes:
                    attribute = SubElement(getCardList, ns0 + 'attributeList')
                    SubElement(attribute, ns0 + 'name', nsmap=NSMAP).text = attr

        if _filter or filter_sq_operator:
            queryType = SubElement(getCardList, ns0 + 'queryType', nsmap=NSMAP)
            if _filter and not filter_sq_operator:
                __filter__ = SubElement(queryType, ns0 + 'filter', nsmap=NSMAP)
                for k, v in _filter.items():
                    SubElement(__filter__, ns0 + str(k), nsmap=NSMAP).text = str(v)

            if filter_sq_operator and not _filter:
                filterOperator = SubElement(queryType, ns0 + 'filterOperator', nsmap=NSMAP)
                for d in filter_sq_operator:
                    if isinstance(d, str):
                        SubElement(filterOperator, ns0 + 'operator', nsmap=NSMAP).text = d
                    elif isinstance(d, list):
                        for r in d:
                            subquery = SubElement(filterOperator, ns0 + 'subquery', nsmap=NSMAP)
                            sq_filter = SubElement(subquery, ns0 + 'filter', nsmap=NSMAP)
                            for k, v in r.items():
                                SubElement(sq_filter, ns0 + str(k), nsmap=NSMAP).text = str(v)

        if order_type:
            orderType = SubElement(getCardList, ns0 + 'orderType', nsmap=NSMAP)
            for k, v in order_type.items():
                SubElement(orderType, ns0 + k, nsmap=NSMAP).text = v

        if limit:
            SubElement(getCardList, ns0 + 'limit', nsmap=NSMAP).text = str(limit)

        if offset:
            SubElement(getCardList, ns0 + 'offset', nsmap=NSMAP).text = offset

        if full_text_query:
            SubElement(getCardList, ns0 + 'fullTextQuery', nsmap=NSMAP).text = full_text_query

        if cql_query:
            cqlQuery = SubElement(getCardList, ns0 + 'cqlQuery', nsmap=NSMAP)
            SubElement(cqlQuery, ns0 + 'cqlQuery', nsmap=NSMAP).text = str(cql_query)
            if cql_query_params:
                for k, v in cql_query_params.items():
                    parameters = SubElement(cqlQuery, ns0 + 'parameters', nsmap=NSMAP)
                    SubElement(parameters, ns0 + str(k), nsmap=NSMAP).text = str(v)


        self.response = self.__request__()

    def getReference(self, classname, query, order_type=None, limit=None, offset=None, full_text_query=None):
        self.__create_header__()
        getReference = SubElement(self.Body, ns0 + 'getReference', nsmap=NSMAP)
        SubElement(getReference, ns0 + 'query', nsmap=NSMAP).text = query
        if order_type:
            SubElement(getReference, ns0 + 'orderType', nsmap=NSMAP).text = order_type
        if limit:
            SubElement(getReference, ns0 + 'limit', nsmap=NSMAP).text = str(limit)
        if offset:
            SubElement(getReference, ns0 + 'offset', nsmap=NSMAP).text = offset
        if full_text_query:
            SubElement(getReference, ns0 + 'fullTextQuery', nsmap=NSMAP).text = full_text_query
        self.response = self.__request__()

    def getLookupList(self, lookup_type, value=None, parent_list=False):
        self.__create_header__()
        getLookupList = SubElement(self.Body, ns0 + 'getLookupList', nsmap=NSMAP)
        SubElement(getLookupList, ns0 + 'type', nsmap=NSMAP).text = lookup_type
        if value:
            SubElement(getLookupList, ns0 + 'value', nsmap=NSMAP).text = value
        if parent_list:
            SubElement(getLookupList, ns0 + 'parentList', nsmap=NSMAP).text = str(parent_list)

        self.response = self.__request__()

    def getLookupListByCode(self, lookup_type=None, code=None, parent_list=False):
        self.__create_header__()
        getLookupListByCode = SubElement(self.Body, ns0 + 'getLookupListExt', nsmap=NSMAP)
        if lookup_type:
            SubElement(getLookupListByCode, ns0 + 'type', nsmap=NSMAP).text = lookup_type
        if code:
            SubElement(getLookupListByCode, ns0 + 'value', nsmap=NSMAP).text = code
        if parent_list:
            SubElement(getLookupListByCode, ns0 + 'parentList', nsmap=NSMAP).text = str(parent_list)

        self.response = self.__request__()

    def getLookupById(self, lookup_id):
        self.__create_header__()
        getLookupById = SubElement(self.Body, ns0 + 'getLookupById', nsmap=NSMAP)
        SubElement(getLookupById, ns0 + 'id', nsmap=NSMAP).text = str(lookup_id)

        self.response = self.__request__()

    def deleteLookup(self, lookup_id):
        self.__create_header__()
        deleteLookup = SubElement(self.Body, ns0 + 'deleteLookup', nsmap=NSMAP)
        SubElement(deleteLookup, ns0 + 'id', nsmap=NSMAP).text = str(lookup_id)

        self.response = self.__request__()

    def updateLookup(self, lookup_type, code, description, lookup_id, notes=None, parent_id=None, position=None):
        self.__create_header__()
        updateLookup = SubElement(self.Body, ns0 + 'updateLookup', nsmap=NSMAP)
        lookup = SubElement(updateLookup, ns0 + 'lookup', nsmap=NSMAP)
        SubElement(lookup, ns0 + 'code', nsmap=NSMAP).text = str(code)
        SubElement(lookup, ns0 + 'description', nsmap=NSMAP).text = str(description)
        SubElement(lookup, ns0 + 'id', nsmap=NSMAP).text = str(lookup_id)

        if notes:
            SubElement(lookup, ns0 + 'notes', nsmap=NSMAP).text = str(notes)

        if parent_id and position:
            SubElement(lookup, ns0 + 'parentId', nsmap=NSMAP).text = str(parent_id)
            SubElement(lookup, ns0 + 'position', nsmap=NSMAP).text = str(position)

        self.response = self.__request__()

    def createLookup(self, lookup_type, code, description, lookup_id, notes=None, parent_id=None, position=None):
        self.__create_header__()
        createLookup = SubElement(self.Body, ns0 + 'createLookup', nsmap=NSMAP)
        lookup = SubElement(createLookup, ns0 + 'lookup', nsmap=NSMAP)
        SubElement(lookup, ns0 + 'code', nsmap=NSMAP).text = str(code)
        SubElement(lookup, ns0 + 'description', nsmap=NSMAP).text = str(description)
        SubElement(lookup, ns0 + 'id', nsmap=NSMAP).text = str(lookup_id)

        if notes:
            SubElement(lookup, ns0 + 'notes', nsmap=NSMAP).text = str(notes)

        if parent_id and position:
            SubElement(lookup, ns0 + 'parentId', nsmap=NSMAP).text = str(parent_id)
            SubElement(lookup, ns0 + 'position', nsmap=NSMAP).text = str(position)

        self.response = self.__request__()

    def createRelation(self, domain_name, class_1_name, card_1_id,
                        class_2_name, card_2_id, status, begin_date,
                        end_date):
        self.__create_header__()
        createRelation = SubElement(self.Body, ns0 + 'createRelation', nsmap=NSMAP)
        relation = SubElement(createRelation, ns0 + 'relation', nsmap=NSMAP)
        SubElement(relation, ns0 + 'domainName', nsmap=NSMAP).text = str(domain_name)
        SubElement(relation, ns0 + 'class1Name', nsmap=NSMAP).text = str(class_1_name)
        SubElement(relation, ns0 + 'card1Id', nsmap=NSMAP).text = str(class_1_id)
        SubElement(relation, ns0 + 'class2Name', nsmap=NSMAP).text = str(class_2_name)
        SubElement(relation, ns0 + 'card2Id', nsmap=NSMAP).text = str(class_2_id)
        SubElement(relation, ns0 + 'status', nsmap=NSMAP).text = str(status)
        SubElement(relation, ns0 + 'beginDate', nsmap=NSMAP).text = str(begin_date)
        SubElement(relation, ns0 + 'endDate', nsmap=NSMAP).text = str(end_date)

        self.response = self.__request__()

    def createRelationWithAttributes(self, domain_name, class_1_name, card_1_id,
                        class_2_name, card_2_id, status, begin_date,
                                     end_date, attributes):
        self.__create_header__()
        createRelationWithAttributes = SubElement(self.Body, ns0 + 'createRelationWithAttributes', nsmap=NSMAP)
        relation = SubElement(createRelationWithAttributes, ns0 + 'relation', nsmap=NSMAP)
        SubElement(relation, ns0 + 'domainName', nsmap=NSMAP).text = str(domain_name)
        SubElement(relation, ns0 + 'class1Name', nsmap=NSMAP).text = str(class_1_name)
        SubElement(relation, ns0 + 'card1Id', nsmap=NSMAP).text = str(class_1_id)
        SubElement(relation, ns0 + 'class2Name', nsmap=NSMAP).text = str(class_2_name)
        SubElement(relation, ns0 + 'card2Id', nsmap=NSMAP).text = str(class_2_id)
        SubElement(relation, ns0 + 'status', nsmap=NSMAP).text = str(status)
        SubElement(relation, ns0 + 'beginDate', nsmap=NSMAP).text = str(begin_date)
        SubElement(relation, ns0 + 'endDate', nsmap=NSMAP).text = str(end_date)

        if attributes:
            attributeList = SubElement(relation, ns0 + 'attributeList', nsmap=NSMAP)
            for k, v in attributes.items():
                SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)

        self.response = self.__request__()

    def updateRelation(self, domain_name, class_1_name, card_1_id,
                        class_2_name, card_2_id, status, begin_date,
                        end_date):
        self.__create_header__()
        updateRelation = SubElement(self.Body, ns0 + 'updateRelation', nsmap=NSMAP)
        relation = SubElement(updateRelation, ns0 + 'relation', nsmap=NSMAP)
        SubElement(relation, ns0 + 'domainName', nsmap=NSMAP).text = str(domain_name)
        SubElement(relation, ns0 + 'class1Name', nsmap=NSMAP).text = str(class_1_name)
        SubElement(relation, ns0 + 'card1Id', nsmap=NSMAP).text = str(class_1_id)
        SubElement(relation, ns0 + 'class2Name', nsmap=NSMAP).text = str(class_2_name)
        SubElement(relation, ns0 + 'card2Id', nsmap=NSMAP).text = str(class_2_id)
        SubElement(relation, ns0 + 'status', nsmap=NSMAP).text = str(status)
        SubElement(relation, ns0 + 'beginDate', nsmap=NSMAP).text = str(begin_date)
        SubElement(relation, ns0 + 'endDate', nsmap=NSMAP).text = str(end_date)

        self.response = self.__request__()

    def deleteRelation(self, domain_name, class_1_name, card_1_id,
                        class_2_name, card_2_id, status, begin_date,
                        end_date):
        self.__create_header__()
        deleteRelation = SubElement(self.Body, ns0 + 'deleteRelation', nsmap=NSMAP)
        relation = SubElement(deleteRelation, ns0 + 'relation', nsmap=NSMAP)
        SubElement(relation, ns0 + 'domainName', nsmap=NSMAP).text = str(domain_name)
        SubElement(relation, ns0 + 'class1Name', nsmap=NSMAP).text = str(class_1_name)
        SubElement(relation, ns0 + 'card1Id', nsmap=NSMAP).text = str(class_1_id)
        SubElement(relation, ns0 + 'class2Name', nsmap=NSMAP).text = str(class_2_name)
        SubElement(relation, ns0 + 'card2Id', nsmap=NSMAP).text = str(class_2_id)
        SubElement(relation, ns0 + 'status', nsmap=NSMAP).text = str(status)
        SubElement(relation, ns0 + 'beginDate', nsmap=NSMAP).text = str(begin_date)
        SubElement(relation, ns0 + 'endDate', nsmap=NSMAP).text = str(end_date)

        self.response = self.__request__()

    def getRelationAttributes(self, domain_name, class_1_name, card_1_id,
                        class_2_name, card_2_id, status, begin_date,
                        end_date):
        self.__create_header__()
        getRelationAttributes = SubElement(self.Body, ns0 + 'getRelationAttributes', nsmap=NSMAP)
        relation = SubElement(getRelationAttributes, ns0 + 'relation', nsmap=NSMAP)
        SubElement(relation, ns0 + 'domainName', nsmap=NSMAP).text = str(domain_name)
        SubElement(relation, ns0 + 'class1Name', nsmap=NSMAP).text = str(class_1_name)
        SubElement(relation, ns0 + 'card1Id', nsmap=NSMAP).text = str(class_1_id)
        SubElement(relation, ns0 + 'class2Name', nsmap=NSMAP).text = str(class_2_name)
        SubElement(relation, ns0 + 'card2Id', nsmap=NSMAP).text = str(class_2_id)
        SubElement(relation, ns0 + 'status', nsmap=NSMAP).text = str(status)
        SubElement(relation, ns0 + 'beginDate', nsmap=NSMAP).text = str(begin_date)
        SubElement(relation, ns0 + 'endDate', nsmap=NSMAP).text = str(end_date)

        self.response = self.__request__()

    def getRelationList(self, domain_name=None, classname=None, card_id=None):
        self.__create_header__()
        getRelationList = SubElement(self.Body, ns0 + 'getRelationList', nsmap=NSMAP)
        if domain_name:
            SubElement(getRelationList, ns0 + 'domain', nsmap=NSMAP).text = str(domain_name)
        if classname:
            SubElement(getRelationList, ns0 + 'className', nsmap=NSMAP).text = str(classname)
        if card_id:
            SubElement(getRelationList, ns0 + 'cardId', nsmap=NSMAP).text = str(card_id)

        self.response = self.__request__()

    def getRelationListExt(self, domain_name=None, classname=None, card_id=None):
        self.__create_header__()
        getRelationListExt = SubElement(self.Body, ns0 + 'getRelationListExt', nsmap=NSMAP)
        if domain_name:
            SubElement(getRelationListExt, ns0 + 'domain', nsmap=NSMAP).text = str(domain_name)
        if classname:
            SubElement(getRelationListExt, ns0 + 'className', nsmap=NSMAP).text = str(classname)
        if card_id:
            SubElement(getRelationListExt, ns0 + 'cardId', nsmap=NSMAP).text = str(card_id)

        self.response = self.__request__()

    def startWorkflow(self, classname, attributes=None, metadata=None, complete_task=False):
        self.__create_header__()
        startWorkflow = SubElement(self.Body, ns0 + 'startWorkflow', nsmap=NSMAP)
        card = SubElement(startWorkflow, ns0 + 'card', nsmap=NSMAP)
        SubElement(card, ns0 + 'className', nsmap=NSMAP).text = classname

        if attributes:
            attributeList = SubElement(card, ns0 + 'attributeList', nsmap=NSMAP)
            for k, v in attributes.items():
                SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)

        if metadata:
            metadata = SubElement(card, ns0 + 'metadata', nsmap=NSMAP)
            for k, v in metadata.items():
                SubElement(metadata, ns0 + str(k), nsmap=NSMAP).text = str(v)
        SubElement(startWorkflow, ns0 + 'completeTask', nsmap=NSMAP).text = complete_task

        self.response = self.__request__()

    def updateWorkflow(self, classname, cardid, attributes=None, metadata=None, complete_task=False):
        self.__create_header__()
        updateWorkflow = SubElement(self.Body, ns0 + 'updateWorkflow', nsmap=NSMAP)
        card = SubElement(startWorkflow, ns0 + 'card', nsmap=NSMAP)
        SubElement(card, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(card, ns0 + 'Id', nsmap=NSMAP).text = str(cardid)

        if attributes:
            attributeList = SubElement(card, ns0 + 'attributeList', nsmap=NSMAP)
            for k, v in attributes.items():
                SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)

        if metadata:
            metadata = SubElement(card, ns0 + 'metadata', nsmap=NSMAP)
            for k, v in metadata.items():
                SubElement(metadata, ns0 + str(k), nsmap=NSMAP).text = str(v)
        SubElement(startWorkflow, ns0 + 'completeTask', nsmap=NSMAP).text = complete_task

        self.response = self.__request__()

    def resumeWorkflow(self, classname, cardid, attributes=None, metadata=None, complete_task=False):
        self.__create_header__()
        resumeWorkflow = SubElement(self.Body, ns0 + 'resumeWorkflow', nsmap=NSMAP)
        card = SubElement(startWorkflow, ns0 + 'card', nsmap=NSMAP)
        SubElement(card, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(card, ns0 + 'Id', nsmap=NSMAP).text = str(cardid)

        if attributes:
            attributeList = SubElement(card, ns0 + 'attributeList', nsmap=NSMAP)
            for k, v in attributes.items():
                SubElement(attributeList, ns0 + 'name', nsmap=NSMAP).text = str(k)
                SubElement(attributeList, ns0 + 'value', nsmap=NSMAP).text = str(v)

        if metadata:
            metadata = SubElement(card, ns0 + 'metadata', nsmap=NSMAP)
            for k, v in metadata.items():
                SubElement(metadata, ns0 + str(k), nsmap=NSMAP).text = str(v)
        SubElement(startWorkflow, ns0 + 'completeTask', nsmap=NSMAP).text = complete_task

        self.response = self.__request__()

    def getAttachmentList(self, classname, cardid=None):
        self.__create_header__()
        getAttachmentList = SubElement(self.Body, ns0 + 'getAttachmentList', nsmap=NSMAP)
        SubElement(getAttachmentList, ns0 + 'className', nsmap=NSMAP).text = classname
        if cardid:
            SubElement(getAttachmentList, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        self.response = self.__request__()

    def uploadAttachment(self, classname, cardid, _file=None, filename=None, category=None, description=None):
        self.__create_header__()
        uploadAttachment = SubElement(self.Body, ns0 + 'uploadAttachment', nsmap=NSMAP)
        SubElement(uploadAttachment, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(uploadAttachment, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)
        SubElement(uploadAttachment, ns0 + 'file', nsmap=NSMAP).text = str(_file)

        SubElement(uploadAttachment, ns0 + 'fileName', nsmap=NSMAP).text = str(filename)
        SubElement(uploadAttachment, ns0 + 'category', nsmap=NSMAP).text = str(category)
        SubElement(uploadAttachment, ns0 + 'description', nsmap=NSMAP).text = str(description)

        self.response = self.__request__()

    def downloadAttachment(self, classname, cardid, filename=None):
        self.__create_header__()
        downloadAttachment = SubElement(self.Body, ns0 + 'downloadAttachment', nsmap=NSMAP)
        SubElement(downloadAttachment, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(downloadAttachment, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        SubElement(downloadAttachment, ns0 + 'fileName', nsmap=NSMAP).text = str(filename)

        self.response = self.__request__()

    def deleteAttachment(self, classname, cardid, filename=None):
        self.__create_header__()
        deleteAttachment = SubElement(self.Body, ns0 + 'deleteAttachment', nsmap=NSMAP)
        SubElement(deleteAttachment, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(deleteAttachment, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        SubElement(deleteAttachment, ns0 + 'fileName', nsmap=NSMAP).text = str(filename)

        self.response = self.__request__()

    def updateAttachmentDescription(self, classname, cardid, filename=None, description=None):
        self.__create_header__()
        updateAttachmentDescription = SubElement(self.Body, ns0 + 'updateAttachmentDescription', nsmap=NSMAP)
        SubElement(updateAttachmentDescription, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(updateAttachmentDescription, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        SubElement(updateAttachmentDescription, ns0 + 'fileName', nsmap=NSMAP).text = str(filename)
        SubElement(updateAttachmentDescription, ns0 + 'description', nsmap=NSMAP).text = str(description)

        self.response = self.__request__()


    def getProcessHelp(self, classname, cardid):
        self.__create_header__()
        getProcessHelp = SubElement(self.Body, ns0 + 'getProcessHelp', nsmap=NSMAP)
        SubElement(getActivityObjects, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(getActivityObjects, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        self.response = self.__request__()

    def getActivityObjects(self, classname, cardid):
        self.__create_header__()
        getActivityObjects = SubElement(self.Body, ns0 + 'getActivityObjects', nsmap=NSMAP)
        SubElement(getActivityObjects, ns0 + 'className', nsmap=NSMAP).text = classname
        SubElement(getActivityObjects, ns0 + 'cardId', nsmap=NSMAP).text = str(cardid)

        self.response = self.__request__()

    def getAttributeList(self, classname):
        self.__create_header__()
        getAttributeList = SubElement(self.Body, ns0 + 'getAttributeList', nsmap=NSMAP)
        SubElement(getAttributeList, ns0 + 'className', nsmap=NSMAP).text = classname

        self.response = self.__request__()

    def getActivityMenuSchema(self,):
        self.__create_header__()
        SubElement(self.Body, ns0 + 'getActivityMenuSchema', nsmap=NSMAP)

        self.response = self.__request__()

    def getCardMenuSchema(self,):
        self.__create_header__()
        SubElement(self.Body, ns0 + 'getCardMenuSchema', nsmap=NSMAP)

        self.response = self.__request__()

    def getMenuSchema(self,):
        self.__create_header__()
        SubElement(self.Body, ns0 + 'getMenuSchema', nsmap=NSMAP)

        self.response = self.__request__()

    def __request__(self,):
        if self.verbose:
            print(tostring(self.Envelope, pretty_print=True))
        encoded_request = tostring(self.Envelope)
        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "Content-Length": str(len(encoded_request)),
            "SOAPAction": ""
        }
        resp = requests.post(url=self.url, headers = headers, data = encoded_request)
        if resp.text:
            response = re.findall('(<soap:Envelope.*?</soap:Envelope>)', resp.text)[0]
            if self.verbose:
                print(tostring(fromstring(response), encoding='UTF-8', pretty_print=True))
            self.response = fromstring(response)
            r = self.response.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
            try:
                nsreturn = r.getchildren()[0][0] # ns2:return
            except:
                nsreturn = r.getchildren()[0]

            if nsreturn.tag == 'faultcode':
                nsreturn = r.getchildren()[0]
            return xml2dict(nsreturn)


if __name__ == '__main__':
    import unittest
    t = CMDBuild(
        username='admin',
        password='3$rFvCdE',
        url='http://10.244.244.128/cmdbuild/services/soap/Webservices?wsdl',
        use_digest = False,
        verbose = False
    )
    t.createCard('Hosts', [{'name':'daas', 'value':'vdacvdas'}])
