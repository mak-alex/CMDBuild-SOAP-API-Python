import unittest
from cmdbuild import CMDBuild as cmdbuild

url = 'http://10.244.244.128/cmdbuild/services/soap/Webservices?wsdl'
t = cmdbuild(
    username='admin', password='3$rFvCdE',
    url=url, debug=False, use_digest=False
)
# this tests for model Ltd. Kazniie Innovation
# if you want to run this test, please rename the 'classname' for all methods


class Test_CMDBuild_SOAP_API_Methods(unittest.TestCase):
    def test_1_create_card(self,):
        self.assertIsNotNone(t.create_card('AddressesIPv4', {
            'Address': '192.192.192.192/24'}))

    def test_2_update_card(self,):
        card = t.get_card_list('AddressesIPv4', None, {
            'name': 'Address',
            'operator': 'EQUALS',
            'value': '192.192.192.192/24'
        })
        self.assertIsNotNone(
            t.update_card(
                'AddressesIPv4',
                card['cards'][0]['id'],
                {'Address': '192.192.192.192/24'}
            )
        )

    def test_3_delete_card(self,):
        card = t.get_card_list('AddressesIPv4', None, {
            'name': 'Address',
            'operator': 'EQUALS',
            'value': '192.192.192.192/24'
        })
        self.assertIsNotNone(t.delete_card('AddressesIPv4',
                                           card['cards'][0]['id']))

    def test_get_reference(self,):
        self.assertIsNotNone(t.get_reference(classname='Hosts'))

    def test_get_card_list(self,):
        self.assertIsNotNone(t.get_card_list(classname='Hosts'))

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
    unittest.main(verbosity=2)
