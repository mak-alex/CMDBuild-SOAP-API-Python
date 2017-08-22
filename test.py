import json
import unittest
from cmdbuild import CMDBuild as cmdbuild
t = cmdbuild(
    username='admin',
    password='3$rFvCdE',
    url='http://10.244.244.128/cmdbuild/services/soap/Webservices?wsdl',
    verbose=False,
    debug=False
)


class Test_CMDBuild_SOAP_API_Methods(unittest.TestCase):
    def test_create_new_instance_cmdbuild(self,):
        self.assertIsNotNone(t)

    def test_get_reference(self,):
        self.assertIsNotNone(t.get_reference(classname='Hosts'))

    def test_get_card_list(self,):
        cards = t.get_card_list(classname='Hosts')
        self.assertIsNotNone(cards)

    def test_get_relation_list(self,):
        self.assertIsNotNone(t.get_relation_list(classname='Hosts'))

    def test_get_relation_list_ext(self,):
        self.assertIsNotNone(t.get_relation_list_ext(classname='Hosts'))

    def test_get_lookup_list(self,):
        self.assertIsNotNone(t.get_lookup_list(lookup_type='LOC_TYPE'))

    def test_get_attribute_list(self,):
        self.assertIsNotNone(t.get_attribute_list(classname='Hosts'))

    def test_get_attachment_list(self,):
        self.assertIsNotNone(t.get_attachment_list(classname='Hosts'))

    def test_get_activity_menu_schema(self,):
        self.assertIsNotNone(t.get_activity_menu_schema())

    def test_get_menu_schema(self,):
        self.assertIsNotNone(t.get_menu_schema())

    def test_get_card_menu_schema(self,):
        self.assertIsNotNone(t.get_card_menu_schema())


if __name__ == '__main__':
    unittest.main()


