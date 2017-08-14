#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
import json
from suds.client import Client
from suds.plugin import MessagePlugin
from suds.wsse import *

# todo: реализовать работу по токену
# todo: дописать остальные методы
# todo: провести рефакторинг и задокументировать методы

if sys.version_info[:2] <= (2, 7):
    reload(sys)
    sys.setdefaultencoding('utf-8')


class NamespaceAndResponseCorrectionPlugin(MessagePlugin):
    def __init__(self):
        pass

    def received(self, context):
        if sys.version_info[:2] >= (2, 7):
            reply_new = re.findall(
                "<soap:Envelope.+</soap:Envelope>",
                context.reply.decode('utf-8'), re.DOTALL
            )[0]
        context.reply = reply_new

    def marshalled(self, context):
        url = 'http://docs.oasis-open.org/wss/2004/01/'
        pass_type = url + 'oasis-200401-wss-username-token-profile-1.0#PasswordText'
        password = context.envelope \
            .getChild('Header') \
            .getChild('Security') \
            .getChild('UsernameToken') \
            .getChild('Password')
        password.set('Type', pass_type)


class CMDBuild:
    """
    CMDBuild SOAP API Library
    Example:
        cmdbuild = CMDBuild('admin', '3$rFvCdE', '10.244.244.128')
        cmdbuild.auth()
        response = cmdbuild.get_card_list('Hosts')
        if response:
            print(json.dumps(response, indent=2))  # Z2C format response
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

    def __init__(self, username=None, password=None, ip='localhost', verbose=True, _debug=False):
        self.username = username
        self.password = password
        self.ip = ip
        self.url = 'http://{}/cmdbuild/services/soap/Webservices?wsdl'.format(self.ip)
        self.client = None
        if self.username and self.password:
            self.auth(self.username, self.password)

    def auth(self, username=None, password=None):
        if not self.username and not self.password:
            if username and password:
                self.username = username
                self.password = password
            else:
                print('`username\' and/or `password\' can\'t be empty')
                sys.exit(-1)
        try:
            self.client = Client(self.url, plugins=[NamespaceAndResponseCorrectionPlugin()])
        except Exception as e:
            print('Failed to create a new instance of the SUDS, '
                  'check the settings are correct, ip address, etc.')
            import requests
            try:
                resp = requests.get(self.url)
                if resp.status_code:
                    print("Oops! URL address: {}  is not available".format(self.url))
            except requests.ConnectionError as e:
                print("Oops! URL address: {}  is not available".format(self.url))
            sys.exit(-1)

        try:
            security = Security()
            if self.username and self.password:
                token = UsernameToken(self.username, self.password)
                token.setcreated()
            security.tokens.append(token)
        except:
            print(
                'Failed to create or add a token, args: username={0}, password={1}'.format(self.username,
                                                                                           self.password))
            sys.exit(-1)
        self.client.set_options(wsse=security)

    def get_card(self, classname, card_id, attributes_list=None):
        attribute_list = []
        if attributes_list:
            attribute = self.client.factory.create('ns0:attribute')
            for i, item in enumerate(attributes_list):
                attribute.name = attributes_list[i]
            attribute_list.append(attribute)

        try:
            result = self.client.service.getCard(className=classname, cardId=card_id, attributeList=attributes_list)
            if result:
                print('Card classname: \'{0}\', id: \'{1}\' - obtained'.format(classname, card_id))
        except:
            print('Failed to get card for classname: {0}, id: {1}'.format(classname, card_id))
            sys.exit()
        return decode(result)

    def get_card_history(self, classname, card_id, limit=None, offset=None):
        try:
            result = self.client.service.getCardHistory(className=classname, cardId=card_id, limit=limit, offset=offset)
            if result:
                if result[0] == 0:
                    sys.exit()
                print('Card history classname: \'{0}\', id: \'{1}\' - obtained'.format(classname, card_id))
        except:
            print('Failed to get history card for classname: \'{0}\', id: \'{1}\''.format(classname, card_id))
            sys.exit()
        return decode(result)

    def get_card_list(self, classname, attributes_list=None, _filter=None, filter_sq_operator=None,
                      order_type=None, limit=None, offset=None, full_text_query=None, cql_query=None,
                      cql_query_parameters=None):
        attribute_list = []
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

        try:
            result = self.client.service.getCardList(className=classname, attributeList=attribute_list, queryType=query)
            if not result[0]:
                print('Failed to get cards for classname: {0}, total rows: {1}'.format(classname, result[0]))
                sys.exit()
            else:
                if _filter:
                    print('Cards classname: \'{0}\' with filter: {1}, total rows: \'{2}\' - obtained'.format(classname,
                                                                                                             _filter,
                                                                                                             result[1]))
                else:
                    print('Cards classname: \'{0}\', total rows: \'{1}\' - obtained'.format(classname, result[1]))
        except:
            print('Failed to get cards for classname: {}'.format(classname))
            sys.exit()

        return decode(result)

    def delete_card(self, classname, card_id):
        try:
            result = self.client.service.deleteCard(className=classname, cardId=card_id)
            print('Card classname: \'{0}\', id: \'{1}\' - removed'.format(classname, card_id))
        except:
            print('Can\'t delete a card, class name: \'{0}\', ID: \'{1}\''.format(classname, card_id))
            sys.exit()
        return decode(result)

    def create_card(self, classname, attributes_list, metadata=None):
        cardType = self.client.factory.create('ns0:cardType')
        cardType.className = classname
        if attributes_list:
            attribute_list = []
            attribute = self.client.factory.create('ns0:attributeList')
            if isinstance(attributes_list, list):
                for attributes in attributes_list:
                    for k, v in attributes.items():
                        attribute.name = k
                        attribute.value = v
                    attribute_list.append(attribute)
            else:
                for k, v in attributes_list.items():
                    attribute.name = k
                    attribute.value = v
                attribute_list.append(attribute)
            cardType.attributeList = attribute_list

        if metadata:
            cardType.metadata = metadata

        try:
            result = self.client.service.createCard(cardType)
            if result:
                print(
                    'Card classname: \'{0}\', id: \'{1}\' with: {2} - created'.format(classname, result,
                                                                                      attribute_list))
        except:
            for k, v in attributes_list.items():
                filter = {'name': k, 'operator': 'EQUALS', 'value': v}
            print('Don\'t create card classname: \'{0}\' with: {1},  maybe exists'.format(classname, attribute_list))
            print("Attempt getting card classname: {0}, with filter: {{\"name\":{name}, \"operator\":{operator}, "
                  "\"value\":{value}}}".format(classname, **filter))
            result = self.get_card_list(classname, _filter=filter)
        if isinstance(result, dict):
            return result
        else:
            return decode(result)

    def update_card(self, classname, card_id, attributes_list, metadata=None, begin_date=None):
        cardType = self.client.factory.create('ns0:card')
        cardType.className = classname
        cardType.id = card_id
        cardType.beginDate = begin_date
        if attributes_list:
            attribute_list = []
            attribute = self.client.factory.create('ns0:attributeList')
            if isinstance(attributes_list, list):
                for attributes in attributes_list:
                    for k, v in attributes.items():
                        attribute.name = k
                        attribute.value = v
                    attribute_list.append(attribute)
            else:
                for k, v in attributes_list.items():
                    attribute.name = k
                    attribute.value = v
                attribute_list.append(attribute)
            cardType.attributeList = attribute_list

        if metadata:
            cardType.metadata = metadata

        try:
            result = self.client.service.updateCard(cardType)
            if result:
                print(
                    'Card classname: \'{0}\', id: \'{1}\' with attributes: \'{2}\' - updated'.format(classname, card_id,
                                                                                                     attribute_list))
        except:
            print('Card classname: \'{0}\', id: \'{1}\' with attributes: \'{2}\' - can\'t be updated'.format(classname,
                                                                                                             card_id,
                                                                                                             attribute_list))
            sys.exit()
        return decode(result)

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
        except:
            sys.exit()

        return decode(result)

    def delete_lookup(self, lookup_id):
        result = self.client.service.deleteLookup(lookupId=lookup_id)
        return decode(result)

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
        except:
            sys.exit()

        return decode(result)

    def get_lookup_list(self, lookup_type, value, parent_list):
        result = self.client.service.getLookupList(lookup_type, value, parent_list)
        return decode(result)

    def get_lookup_by_id(self, lookup_id):
        result = self.client.service.getLookupById(lookup_id)
        return decode(result)

    def create_relation(self):
        result = self.client.service.createRelation()
        return decode(result)

    def delete_relation(self):
        result = self.client.service.deleteRelation()
        return decode(result)

    def get_relation_list(self, domain, classname, card_id):
        result = self.client.service.getRelationList(domain=domain, className=classname, cardId=card_id)
        return decode(result)

    def get_relation_history(self):
        result = self.client.service.getRelationHistory()
        return decode(result)

    def start_workflow(self):
        result = self.client.service.startWorkflow()
        return decode(result)

    def update_workflow(self):
        result = self.client.service.updateWorkflow()
        return decode(result)

    def upload_attachment(self):
        result = self.client.service.uploadAttachment()
        return decode(result)

    def download_attachment(self):
        result = self.client.service.downloadAttachment()
        return decode(result)

    def delete_attachment(self):
        result = self.client.service.deleteAttachment()
        return decode(result)

    def update_attachment(self):
        result = self.client.service.updateAttachment()
        return decode(result)

    def get_menu_schema(self):
        result = self.client.service.getMenuSchema()
        return decode(result)

    def get_card_menu_schema(self):
        result = self.client.service.getCardMenuSchema()
        return decode(result)


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
            outtab['Id'] = {cards: {}}
        else:
            if cards['cards']:
                cards = cards['cards']
            else:
                cards = cards['card']
            for card in cards:
                _id = card['id']
                outtab['Id'][_id] = {}
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
                                outtab['Id'][_id][key] = value
                            else:
                                if value:
                                    outtab['Id'][_id][key] = {
                                        "value": value, "code": code
                                    }
    except Exception as e:
        _id = cards['id']
        outtab['Id'][_id] = {}
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
                        outtab['Id'][_id][key] = value
                    else:
                        if value:
                            outtab['Id'][_id][key] = {
                                "value": value, "code": code
                            }
    return outtab


if __name__ == '__main__':
    cmdbuild = CMDBuild('admin', '3$rFvCdE', '10.244.244.128')
    cmdbuild.auth()

    response = cmdbuild.get_card_list('Hosts')
    if response:
        print(json.dumps(response, indent=2))  # Z2C format response
