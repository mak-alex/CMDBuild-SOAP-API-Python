#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
import sys
import json
import logging
import datetime
from suds.client import Client
from suds.plugin import MessagePlugin
from suds.wsse import UsernameToken, Security
from suds import WebFault

__author__ = "Alexandr Mikhailenko a.k.a Alex M.A.K."
__copyright__ = "Copyright 2017, Ltd Kazniie Innovation"
__license__ = "MIT"
__version__ = "1.0"
__email__ = "alex-m.a.k@yandex.kz"
__status__ = "Production"

# todo: реализовать работу по токену
# todo: дописать остальные методы
# todo: провести рефакторинг и задокументировать методы


def decode(t):
    def wrapped(*args, **kwargs):
        def _to_dict(obj, key_to_lower=False, json_serialize=False):
            """
                Decode SOAP message to JSON Dict
            """

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
                        data[field].append(_to_dict(item, json_serialize=json_serialize))
                else:
                    data[field] = _to_dict(val, json_serialize=json_serialize)
            return data

        outtab = {'Id': {}}
        cards = _to_dict(t(*args, **kwargs), key_to_lower=False, json_serialize=True)

        if not cards:
            return

        def total_rows(l):
            """
            :param l: dict
            :return: int
            """
            if l:
                if 'totalRows' in l:
                    if isinstance(l['totalRows'], int):
                        return l['totalRows']
                return 1
            else:
                return 0

        total_rows = total_rows(cards)
        if args[0].__class__.verbose:
            if '_filter' in kwargs:
                print('Cards classname: \'{0}\' with filter: {1}, total rows: \'{2}\' - obtained'
                      .format(args[1], kwargs['_filter'], total_rows))
            else:
                print('Cards classname: \'{0}\', total_rows: \'{1}\' - obtained'.format(args[1], total_rows))

        def _do_create(attributes, _id, _outtab):
            for j, attribute in enumerate(attributes):
                if isinstance(attribute, dict):
                    code = None
                    if len(attribute) > 2:
                        code = attribute['code'] or ""
                    key = attribute['name']
                    value = attribute['value'] or ""
                    if key:
                        if not code and value:
                            _outtab['Id'][_id][key] = value
                        else:
                            if value:
                                _outtab['Id'][_id][key] = {"value": value, "code": code}
            return _outtab

        if total_rows >= 2:
            if isinstance(cards, int):
                outtab['Id'] = {cards: {}}
            else:
                if cards['cards']:
                    cards = cards['cards']
                else:
                    cards = cards['card']

                for card in cards:
                    mid = card['id']
                    outtab['Id'][mid] = {}
                    _do_create(card['attributeList'], mid, outtab)
        else:
            if 'cards' in cards:
                cards = cards['cards'][0]
            oid = cards['id']
            outtab['Id'][oid] = {}
            _do_create(cards['attributeList'], oid, outtab)

        return outtab

    return wrapped


class NamespaceAndResponseCorrectionPlugin(MessagePlugin):
    def __init__(self):
        pass

    def received(self, context):
        if sys.version_info[:2] >= (2, 7):
            reply_new = re.findall("<soap:Envelope.+</soap:Envelope>", context.reply.decode('utf-8'), re.DOTALL)[0]
        else:
            reply_new = re.findall("<soap:Envelope.+</soap:Envelope>", context.reply, re.DOTALL)[0]
        context.reply = reply_new

    def marshalled(self, context):
        url = 'http://docs.oasis-open.org/wss/2004/01/'
        passt = url + 'oasis-200401-wss-username-token-profile-1.0#PasswordText'
        password = context.envelope \
            .getChild('Header') \
            .getChild('Security') \
            .getChild('UsernameToken') \
            .getChild('Password')
        password.set('Type', passt)


class CMDBuild:
    """
    CMDBuild SOAP API Library

    Args:
        username (string)
        password (string)
        ip (string)
        verbose (bool)
        debug (bool)

    Example:
        cmdbuild = CMDBuild(username='admin', password='3$rFvCdE', ip='10.244.244.128')
        print(json.dumps(cmdbuild.get_card_list('Hosts'), indent=2))

    Response example:
        {
            Id: {
                "19234289": {
                    "Description": "...",
                    ...
                }
            }
        }

    """

    def __init__(self, username=None, password=None, ip=None, verbose=False, debug=False):
        self.ip = ip
        self.client = None
        self.username = username
        self.password = password
        self.verbose = verbose
        self.__class__.verbose = self.verbose
        self.url = 'http://{}/cmdbuild/services/soap/Webservices?wsdl'.format(self.ip)

        if self.username and self.password:
            self.auth(self.username, self.password)

        if debug:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger('suds.client').setLevel(logging.DEBUG)

    def auth(self, username=None, password=None):
        if not self.username and not self.password:
            if username and password:
                self.username = username
                self.password = password
            else:
                if self.verbose:
                    print('`username\' and/or `password\' can\'t be empty')
                sys.exit(-1)
        try:
            headers = {'Content-Type': 'application/soap+xml; charset="ascii"'}
            self.client = Client(self.url, headers=headers, plugins=[NamespaceAndResponseCorrectionPlugin()])
        except WebFault:
            print('Failed to create a new instance of the SUDS, '
                  'check the settings are correct, ip address, etc.')
            import requests
            try:
                resp = requests.get(self.url)
                if resp.status_code:
                    print("Oops! URL address: {}  is not available".format(self.url))
            except requests.ConnectionError:
                print("Oops! URL address: {}  is not available".format(self.url))
            sys.exit(-1)

        security = Security()

        try:
            token = None
            if self.username and self.password:
                token = UsernameToken(self.username, self.password)
            security.tokens.append(token)
        except WebFault:
            print('Failed to create token, args: username={0}, password={1}'.format(self.username, self.password))
            sys.exit(-1)
        self.client.set_options(wsse=security)

    @decode
    def get_card(self, classname, card_id, attributes_list=None):
        """
        Get card
        :param classname:
        :param card_id:
        :param attributes_list:
        :return: dict
        """
        attribute_list = []
        if attributes_list:
            attribute = self.client.factory.create('ns0:attribute')
            for i, item in enumerate(attributes_list):
                attribute.name = attributes_list[i]
            attribute_list.append(attribute)
        try:
            result = self.client.service.getCard(className=classname, cardId=card_id, attributeList=attributes_list)
        except WebFault:
            print('Failed to get card for classname: {0}, id: {1}'.format(classname, card_id))
            sys.exit()
        return result

    @decode
    def get_card_history(self, classname, card_id, limit=None, offset=None):
        """
        Get card history
        :param classname:
        :param card_id:
        :param limit:
        :param offset:
        :return: dict
        """
        try:
            result = self.client.service.getCardHistory(className=classname, cardId=card_id, limit=limit, offset=offset)
            if result:
                if result[0] == 0:
                    sys.exit()
        except WebFault:
            print('Failed to get history card for classname: \'{0}\', id: \'{1}\''.format(classname, card_id))
            sys.exit()
        return result

    @decode
    def get_card_list(self, classname, attributes_list=None, _filter=None,
                      filter_sq_operator=None, order_type=None, limit=None,
                      offset=None, full_text_query=None, cql_query=None,
                      cql_query_parameters=None):
        """
        Get cards from CDMBuild
        :param classname: string
        :param attributes_list: list
        :param _filter: dict
        :param filter_sq_operator:
        :param order_type:
        :param limit:
        :param offset:
        :param full_text_query:
        :param cql_query:
        :param cql_query_parameters:
        :return: dict
        """
        attributes = []
        query = self.client.factory.create('ns0:query')
        if attributes_list:
            attribute = self.client.factory.create('ns0:attribute')
            for i, item in enumerate(attributes_list):
                attribute.name = attributes_list[i]
            attributes.append(attribute)

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

        try:
            result = self.client.service.getCardList(className=classname, attributeList=attributes, queryType=query)
            if not result[0]:
                print('Failed to get cards for classname: {0}, total rows: {1}'.format(classname, result[0]))
                sys.exit()
        except WebFault:
            print('Failed to get cards for classname: {}'.format(classname))
            sys.exit()

        return result

    def delete_card(self, classname, card_id):
        """

        :param classname:
        :param card_id:
        :return: boolean
        """
        try:
            result = self.client.service.deleteCard(className=classname, cardId=card_id)
            if self.verbose:
                print('Card classname: \'{0}\', id: \'{1}\' - removed'.format(classname, card_id))
        except WebFault:
            print('Can\'t delete a card, class name: \'{0}\', ID: \'{1}\''.format(classname, card_id))
            sys.exit()
        return result

    def create_card(self, classname, attributes_list, metadata=None):
        """

        :param classname:
        :param attributes_list:
        :param metadata:
        :return: int
        """
        cardType = self.client.factory.create('ns0:cardType')
        cardType.className = classname
        attributes = []
        attributeList = self.client.factory.create('ns0:attributeList')
        if attributes_list:
            if isinstance(attributes_list, list):
                for attribute in attributes_list:
                    for k, _v in attribute.items():
                        attributeList.name = k
                        attributeList.value = _v
                    attributes.append(attributeList)
            else:
                for k, _v in attributes_list.items():
                    attributeList.name = k
                    attributeList.value = _v
                attributes.append(attributeList)
            cardType.attributeList = attributes

        if metadata:
            cardType.metadata = metadata

        result = None
        try:
            result = self.client.service.createCard(cardType)
            if result:
                if self.verbose:
                    print('Card classname: \'{0}\', id: \'{1}\' with: {2} - created'
                          .format(classname, result, attributes_list))
        except WebFault:
            if self.verbose:
                print('Don\'t create card classname: \'{0}\' with: {1},  maybe exists'.format(classname, attributes_list))

        return result

    def update_card(self, classname, card_id, attributes_list, metadata=None, begin_date=None):
        """

        :param classname:
        :param card_id:
        :param attributes_list:
        :param metadata:
        :param begin_date:
        :return: boolean
        """
        cardType = self.client.factory.create('ns0:card')
        cardType.className = classname
        cardType.id = card_id
        cardType.beginDate = begin_date
        attributes = []
        attributeList = self.client.factory.create('ns0:attributeList')
        if attributes_list:
            if isinstance(attributes_list, list):
                for attribute in attributes_list:
                    for k, _v in attribute.items():
                        attributeList.name = k
                        attributeList.value = _v
                    attributes.append(attributeList)
            else:
                for k, _v in attributes_list.items():
                    attributeList.name = k
                    attributeList.value = _v
                attributes.append(attributeList)
            cardType.attributeList = attributes

        if metadata:
            cardType.metadata = metadata

        try:
            result = self.client.service.updateCard(cardType)
            if result:
                if self.verbose:
                    print('Card classname: \'{0}\', id: \'{1}\' with attributes: \'{2}\' - updated'
                          .format(classname, card_id, attributes))
        except WebFault:
            if self.verbose:
                print('Card classname: \'{0}\', id: \'{1}\' with attributes: \'{2}\' - can\'t be updated'
                      .format(classname, card_id, attributes))
            sys.exit()
        return result

    def create_lookup(self, lookup_type, code, description, lookup_id=None, notes=None, parent_id=None, position=None):
        lookup = self.client.factory.create('ns0:lookup')
        lookup.code = code
        lookup.description = description
        if lookup_id:
            lookup.id = lookup_id
        if notes:
            lookup.notes = notes
        if parent_id and position:
            lookup.parentId = parent_id
            lookup.position = position
        lookup.type = lookup_type
        try:
            result = self.client.service.createLookup(lookup)
        except WebFault:
            sys.exit()

        return result

    def delete_lookup(self, lookup_id):
        result = self.client.service.deleteLookup(lookupId=lookup_id)
        return result

    def update_lookup(self, lookup_type, code, description, lookup_id=None, notes=None, parent_id=None, position=None):
        lookup = self.client.factory.create('ns0:lookup')
        lookup.code = code
        lookup.description = description
        if lookup_id:
            lookup.id = lookup_id
        if notes:
            lookup.notes = notes
        if parent_id and position:
            lookup.parentId = parent_id
            lookup.position = position
        lookup.type = lookup_type
        try:
            result = self.client.service.updateLookup(lookup)
        except WebFault:
            sys.exit()

        return result

    def get_lookup_list(self, lookup_type, value, parent_list):
        result = self.client.service.getLookupList(lookup_type, value, parent_list)
        return result

    def get_lookup_by_id(self, lookup_id):
        result = self.client.service.getLookupById(lookup_id)
        return result

    def create_relation(self):
        result = self.client.service.createRelation()
        return result

    def delete_relation(self):
        result = self.client.service.deleteRelation()
        return result

    def get_relation_list(self, domain, classname, card_id):
        result = self.client.service.getRelationList(
            domain=domain, className=classname, cardId=card_id)
        return result

    def get_relation_history(self):
        result = self.client.service.getRelationHistory()
        return result

    def start_workflow(self):
        result = self.client.service.startWorkflow()
        return result

    def update_workflow(self):
        result = self.client.service.updateWorkflow()
        return result

    def upload_attachment(self):
        result = self.client.service.uploadAttachment()
        return result

    def download_attachment(self):
        result = self.client.service.downloadAttachment()
        return result

    def delete_attachment(self):
        result = self.client.service.deleteAttachment()
        return result

    def update_attachment(self):
        result = self.client.service.updateAttachment()
        return result

    def get_menu_schema(self):
        result = self.client.service.getMenuSchema()
        return result

    def get_card_menu_schema(self):
        result = self.client.service.getCardMenuSchema()
        return result

