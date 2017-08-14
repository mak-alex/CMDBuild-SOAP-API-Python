#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
import logging
import lxml.etree as etree
from suds.client import Client
from suds.plugin import MessagePlugin
from suds.wsse import *
import json
import sys

logging.getLogger('suds.client').setLevel(logging.CRITICAL)

if sys.version_info[:2] <= (2, 7):
    reload(sys)
    sys.setdefaultencoding('utf-8')


def xml_pretty_print(doc):
    return etree.tostring(etree.fromstring(doc), pretty_print=True)


class NamespaceAndResponseCorrectionPlugin(MessagePlugin):
    def __init__(self):
        pass

    def received(self, context):
        if sys.version_info[:2] >= (2, 7):
            reply_new = re.findall("<soap:Envelope.+</soap:Envelope>", context.reply.decode('utf-8'), re.DOTALL)[0]
        context.reply = reply_new

    def marshalled(self, context):
        pass_type = 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText'
        password = context.envelope \
            .getChild('Header') \
            .getChild('Security') \
            .getChild('UsernameToken') \
            .getChild('Password')
        password.set('Type', pass_type)


class CMDBuild:
    def __init__(self, username=None, password=None, ip=None):
        self.username = username
        self.password = password
        self.url = 'http://' + ip + '/cmdbuild/services/soap/Webservices?wsdl'
        self.client = None

    def set_credentials(self, username, password):
        if not self.username:
            self.username = username

        if not self.password:
            self.password = password

    def auth(self):
        self.client = Client(self.url, plugins=[NamespaceAndResponseCorrectionPlugin()])
        security = Security()
        token = UsernameToken(self.username, self.password)
        security.tokens.append(token)
        self.client.set_options(wsse=security)
        self.client.set_options(retxml=False)

    def get_card(self, classname, card_id, attributes_list=None):
        attribute_list = []
        if attributes_list:
            attribute = self.client.factory.create('ns0:attribute')
            for i, item in enumerate(attributes_list):
                attribute.name = attributes_list[i]
            attribute_list.append(attribute)

        result = self.client.service.getCard(className=classname, cardId=card_id, attributeList=attributes_list)
        return self.decode(result)

    def get_card_history(self, classname, card_id, limit=None, offset=None):
        result = self.client.service.getCardHistory(className=classname, cardId=card_id, limit=limit, offset=offset)
        return self.decode(result)

    def get_card_list(self, classname, attributes_list=None, _filter=None, filter_sq_operator=None,
                      order_type=None, limit=None, offset=None, full_text_query=None, cql_query=None,
                      cql_query_parameters=None):
        attribute_list = []
        result = None
        try:
            query = self.client.factory.create('ns0:query')
            if attributes_list:
                attribute = self.client.factory.create('ns0:attribute')
                for i, item in enumerate(attributes_list):
                    attribute.name = attributes_list[i]
                attribute_list.append(attribute)

            if _filter or filter_sq_operator:
                if _filter and not filter_sq_operator:
                    query.filter = _filter

            if order_type:
                query.orderType = order_type

            if limit:
                query.limit = limit

            if offset:
                query.offset = offset

            if full_text_query:
                query.fullTextQuery = full_text_query

            if cql_query:
                query.cqlQuery.parameters = cql_query_parameters

            result = self.client.service.getCardList(className=classname, attributeList=attribute_list, queryType=query)
        except:
            sys.exit()
        return self.decode(result)

    def delete_card(self, classname, card_id):
        result = self.client.service.deleteCard(className=classname, cardId=card_id)
        return self.decode(result)

    def create_card(self, classname, attributes_list, metadata=None):
        cardType = self.client.factory.create('ns0:cardType')
        cardType.className = classname
        if attributes_list:
            attribute_list = []
            attribute = self.client.factory.create('ns0:attributeList')
            for k, v in attributes_list.items():
                attribute.name = k
                attribute.value = v
            attribute_list.append(attribute)
            cardType.attributeList = attribute_list

        if metadata:
            cardType.metadata = metadata

        result = None
        try:
            result = self.client.service.createCard(cardType)
        except:
            for k, v in attributes_list.items():
                filter = {'name':k, 'operator':'EQUALS', 'value':v}
            print('Don\'t create card classname: ' + classname + ',  maybe exists')
            print('Filter: {{"name":{name}, "operator":{operator}, "value":{value}}}'.format(**filter))
            result = self.get_card_list(classname, _filter=filter)
        if isinstance(result, dict):
            return result
        else:
            return self.decode(result)

    def update_card(self, classname, id, attributes_list, metadata=None, beginDate=None):
        cardType = self.client.factory.create('ns0:card')
        cardType.className = classname
        cardType.id = id
        cardType.beginDate = beginDate
        if attributes_list:
            attribute_list = []
            attribute = self.client.factory.create('ns0:attributeList')
            for k, v in attributes_list.items():
                attribute.name = k
                attribute.value = v
            attribute_list.append(attribute)
            cardType.attributeList = attribute_list

        if metadata:
            cardType.metadata = metadata

        result = self.client.service.updateCard(cardType)
        return self.decode(result)

    def create_lookup(self,):
        result = self.client.service.createLookup()
        return self.decode(result)

    def delete_lookup(self, lookup_id):
        result = self.client.service.deleteLookup(lookupId=lookup_id)
        return self.decode(result)

    def update_lookup(self):
        result = self.client.service.updateLookup()
        return self.decode(result)

    def get_lookup_list(self):
        result = self.client.service.getLookupList()
        return self.decode(result)

    def get_lookup_by_id(self):
        result = self.client.service.getLookupById()
        return self.decode(result)

    def create_relation(self):
        result = self.client.service.createRelation()
        return self.decode(result)

    def delete_relation(self):
        result = self.client.service.deleteRelation()
        return self.decode(result)

    def get_relation_list(self, domain, classname, card_id):
        result = self.client.service.getRelationList(domain=domain, className=classname, cardId=card_id)
        return self.decode(result)

    def get_relation_history(self):
        result = self.client.service.getRelationHistory()
        return self.decode(result)

    def start_workflow(self):
        result = self.client.service.startWorkflow()
        return self.decode(result)

    def update_workflow(self):
        result = self.client.service.updateWorkflow()
        return self.decode(result)

    def upload_attachment(self):
        result = self.client.service.uploadAttachment()
        return self.decode(result)

    def download_attachment(self):
        result = self.client.service.downloadAttachment()
        return self.decode(result)

    def delete_attachment(self):
        result = self.client.service.deleteAttachment()
        return self.decode(result)

    def update_attachment(self):
        result = self.client.service.updateAttachment()
        return self.decode(result)

    def get_menu_schema(self):
        result = self.client.service.getMenuSchema()
        return self.decode(result)

    def get_card_menu_schema(self):
        result = self.client.service.getCardMenuSchema()
        return self.decode(result)

    @staticmethod
    def decode(_response):
        def suds_to_dict(obj, key_to_lower=False, json_serialize=False):
            import datetime

            if not hasattr(obj, '__keylist__'):
                if json_serialize and isinstance(obj, (datetime.datetime, datetime.time, datetime.date)):
                    return obj.isoformat()
                else:
                    return obj

            data = {}
            fields = obj.__keylist__
            for i, field in enumerate(fields):
                val = getattr(obj, field)
                if key_to_lower:
                    field = field.lower()
                if isinstance(val, list):
                    data[field] = []
                    for item in val:
                        data[field].append(
                            suds_to_dict(item, json_serialize=json_serialize)
                        )
                else:
                    data[field] = suds_to_dict(val, json_serialize=json_serialize)
            return data

        outtab = {'Id': {}}
        cards = suds_to_dict(
            _response, key_to_lower=False, json_serialize=True
        )

        try:
            if isinstance(cards, int):
                outtab['Id'] = cards
            else:
                if cards['cards']:
                    cards = cards['cards']
                else:
                    cards = cards['card']
                for card in cards:
                    id = card['id']
                    outtab['Id'][id] = {}
                    attributes = card['attributeList']
                    for j, attribute in enumerate(attributes):
                        if isinstance(attribute, dict):
                            code = None
                            if len(attribute) > 2:
                                code = attribute['code'] or ""
                            key = attribute['name']
                            value = attribute['value'] or ""
                            if key:
                                if not code and value:
                                    outtab['Id'][id][key] = value
                                else:
                                    if value:
                                        outtab['Id'][id][key] = {
                                            "value": value, "code": code
                                        }
        except:
            id = cards['id']
            outtab['Id'][id] = {}
            attributes = cards['attributeList']
            for j, attribute in enumerate(attributes):
                if isinstance(attribute, dict):
                    code = None
                    if len(attribute) > 2:
                        code = attribute['code'] or ""
                    key = attribute['name']
                    value = attribute['value'] or ""
                    if key:
                        if not code and value:
                            outtab['Id'][id][key] = value
                        else:
                            if value:
                                outtab['Id'][id][key] = {
                                    "value": value, "code": code
                                }
        return outtab


if __name__ == '__main__':
    cmdbuild = CMDBuild('admin', '3$rFvCdE', '10.244.244.128')
    cmdbuild.auth()

    #response = cmdbuild.get_card_list('Hosts')
    #print(json.dumps(response, indent=2))  # Z2C format response
    """ for hostid, v in response['Id'].items():
        if isinstance(hostid, int):
            filter = {'name':'hostid','operator':'EQUALS','value':hostid} # added filter
            v['zItems'] = cmdbuild.get_card_list('zItems', _filter=filter) # get zItems card
            v['zTriggers'] = cmdbuild.get_card_list('ztriggers', _filter=filter) # get ztriggers card
            v['zApplications'] = cmdbuild.get_card_list('zapplications', _filter=filter) # get zapplications card

    """
    response = cmdbuild.create_card('AddressesIPv4',{'Address':'192.168.88.37/24'})
    for id, v in response['Id'].items():
        response = cmdbuild.get_card_history('AddressesIPv4', id)
        #response = cmdbuild.update_card('AddressesIPv4', id, {'Address':'192.168.88.38/24'})
        #response = cmdbuild.delete_card('AddressesIPv4', id)
        print(json.dumps(response, indent=2))  # Z2C format response
