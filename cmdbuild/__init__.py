#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import re
import sys
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

# todo: need to refactor code and eliminate repetition
# todo: need to add skipped tests and check in errors
# todo: need add description for all methods


class CorrectionPlugin(MessagePlugin):
    def __init__(self):
        pass

    def received(self, context):
        env = "<soap:Envelope.+</soap:Envelope>"
        if sys.version_info[:2] >= (2, 7):
            reply_new = re.findall(env, context.reply.decode('utf-8'),
                                   re.DOTALL)[0]
        else:
            reply_new = re.findall(env, context.reply, re.DOTALL)[0]
        context.reply = reply_new

    def marshalled(self, context):
        url = 'http://docs.oasis-open.org/wss/2004/01/'
        passt = url + 'oasis-200401-wss-username-token-profile-1.0' \
                    + '#PasswordText'
        password = context.envelope \
            .getChild('Header') \
            .getChild('Security') \
            .getChild('UsernameToken') \
            .getChild('Password')
        password.set('Type', passt)


class CMDBuild:
    """
    CMDBuild SOAP API Python Wrapper

    CMDBuild is an open source software
    to manage the configuration database (CMDB).
    CMDBuild is compliant with ITIL "best practices" for
    the IT services management according to process-oriented criteria

    Dependencies:
        suds (latest version)

    Args:
        username (string)
        password (string)
        ip (string)
        verbose (bool)
        debug (bool)

    Usage:
        from cmdbuild import CMDBuild as cmdbuild
        cmdbuild = CMDBuild(
            username='admin',
            password='3$rFvCdE',
            url='http://*/Webservices?wsdl'
        )
        #  if, at the time of creating the instance
        # is not specified the username/password,
        # use the method cmdbuild.auth('admin', '3$rFvCdE')
        print(cmdbuild.get_card_list('Hosts'), indent=2)
    """

    def __init__(self, username=None, password=None, url=None, verbose=False, debug=False):
        self.url = url
        self.client = None
        self.username = username
        self.password = password
        self.verbose = verbose
        self.__class__.verbose = self.verbose

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
            self.client = Client(self.url, headers=headers, plugins=[CorrectionPlugin()])
        except WebFault:
            print('Failed to create a new instance of the SUDS, '
                  'check the settings are correct, URL, etc.')
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

    def get_card_list(self, classname, attributes_list=None, _filter=None,
                      filter_sq_operator=None, order_type=None, limit=None,
                      offset=None, full_text_query=None, cql_query=None,
                      cql_query_parameters=None):
        attributes = []
        query = self.client.factory.create('ns0:query')
        attribute = self.client.factory.create('ns0:attribute')
        if attributes_list:
            if isinstance(attributes_list, list):
                for attribute in attributes_list:
                    for k, _v in attribute.items():
                        attribute.name = k
                        attribute.value = _v
                    attributes.append(attribute)
            else:
                for k, _v in attributes_list.items():
                    attribute.name = k
                    attribute.value = _v
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
        try:
            result = self.client.service.deleteLookup(lookupId=lookup_id)
        except WebFault as e:
            print(e)
            sys.exit()
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

    def get_lookup_list(self, lookup_type=None, value=None, parent_list=False):
        result = self.client.service.getLookupList(lookup_type, value, parent_list)
        return result

    def get_lookup_list_by_code(self, lookup_type, lookup_code, parent_list=False):
        try:
            result = self.client.service.getLookupListByCode(lookup_type, lookup_code, parent_list)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_lookup_by_id(self, lookup_id):
        try:
            result = self.client.service.getLookupById(lookup_id)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def create_relation(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date):
        relation = self.client.factory.create('ns0:relation')
        relation.domainName = domain_name
        relation.class1Name = class_1_name
        relation.card1Id = card_1_id
        relation.class2Name = class_2_name
        relation.card2Id = card_2_id
        relation.status = status or 'A'
        relation.beginDate = begin_date
        relation.endDate = end_date
        try:
            result = self.client.service.createRelation(relation)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def create_relation_with_attributes(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date, attributes_list):
        relation = self.client.factory.create('ns0:relation')
        relation.domainName = domain_name
        relation.class1Name = class_1_name
        relation.card1Id = card_1_id
        relation.class2Name = class_2_name
        relation.card2Id = card_2_id
        relation.status = status or 'A'
        relation.beginDate = begin_date
        relation.endDate = end_date
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
            relation.attributeList = attributes
        try:
            result = self.client.service.createRelationWithAttributes(relation)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def delete_relation(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date):
        relation = self.client.factory.create('ns0:relation')
        relation.domainName = domain_name
        relation.class1Name = class_1_name
        relation.card1Id = card_1_id
        relation.class2Name = class_2_name
        relation.card2Id = card_2_id
        relation.status = status or 'A'
        relation.beginDate = begin_date
        relation.endDate = end_date
        try:
            result = self.client.service.deleteRelation(relation)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_relation_list(self, domain=None, classname=None, card_id=None):
        try:
            result = self.client.service.getRelationList(
                domain=domain, className=classname, cardId=card_id)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_relation_list_ext(self, domain=None, classname=None, card_id=None):
        try:
            result = self.client.service.getRelationListExt(
                domain=domain, className=classname, cardId=card_id)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_relation_history(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date):
        relation = self.client.factory.create('ns0:relation')
        relation.domainName = domain_name
        relation.class1Name = class_1_name
        relation.card1Id = card_1_id
        relation.class2Name = class_2_name
        relation.card2Id = card_2_id
        relation.status = status or 'A'
        relation.beginDate = begin_date
        relation.endDate = end_date
        try:
            result = self.client.service.getRelationHistory(relation)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_relation_attributes(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date):
        relation = self.client.factory.create('ns0:relation')
        relation.domainName = domain_name
        relation.class1Name = class_1_name
        relation.card1Id = card_1_id
        relation.class2Name = class_2_name
        relation.card2Id = card_2_id
        relation.status = status or 'A'
        relation.beginDate = begin_date
        relation.endDate = end_date
        try:
            result = self.client.service.getRelationAttributes(relation)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def start_workflow(self, class_name, card_id, attributes_list, begin_date, user, complete_task):
        card = self.client.factory.create('ns0:card')
        card.className = class_name
        if card_id:
            card.Id = card_id
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
            card.attributeList = attributes
        if begin_date:
            card.beginDate = begin_date
        if user:
            card.user = user
        try:
            result = self.client.service.startWorkflow(card, complete_task)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def update_workflow(self, class_name, card_id, attributes_list, begin_date, user, complete_task):
        card = self.client.factory.create('ns0:card')
        card.className = class_name
        if card_id:
            card.Id = card_id
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
            card.attributeList = attributes
        if begin_date:
            card.beginDate = begin_date
        if user:
            card.user = user
        try:
            result = self.client.service.updateWorkflow(card, complete_task)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def resume_workflow(self, class_name, card_id, attributes_list, begin_date, user, complete_task):
        card = self.client.factory.create('ns0:card')
        card.className = class_name
        if card_id:
            card.Id = card_id
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
            card.attributeList = attributes
        if begin_date:
            card.beginDate = begin_date
        if user:
            card.user = user
        try:
            result = self.client.service.resumeWorkflow(card, complete_task)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_reference(self, classname, query=None, order_type=None, limit=None, offset=None, full_text_query=None):
        try:
            result = self.client.service.getReference(classname, query, order_type, limit, offset, full_text_query)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_attachment_list(self, classname, card_id=None):
        try:
            result = self.client.service.getAttachmentList(classname, card_id)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def upload_attachment(self, class_name, object_id, _file, filename, category, description):
        try:
            result = self.client.service.uploadAttachment(class_name, object_id, _file, filename, category, description)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def download_attachment(self, classname, object_id, filename):
        try:
            result = self.client.service.downloadAttachment(classname, object_id, filename)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def delete_attachment(self, classname, card_id, filename):
        try:
            result = self.client.service.deleteAttachment(classname, card_id, filename)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def update_attachment_description(self, classname, card_id, filename, description):
        try:
            result = self.client.service.updateAttachmentDescription(classname, card_id, filename, description)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_activity_menu_schema(self):
        try:
            result = self.client.service.getActivityMenuSchema()
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_activity_objects(self, classname, card_id):
        try:
            result = self.client.service.getActivityObjects(classname, card_id)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_attribute_list(self, classname):
        try:
            result = self.client.service.getAttributeList(classname)
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_menu_schema(self):
        try:
            result = self.client.service.getMenuSchema()
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_card_menu_schema(self):
        try:
            result = self.client.service.getCardMenuSchema()
        except WebFault as e:
            print(e)
            sys.exit()
        return result

    def get_process_help(self, classname, card_id):
        try:
            result = self.client.service.getProcessHelp(classname, card_id)
        except WebFault as e:
            print(e)
            sys.exit()
        return result
