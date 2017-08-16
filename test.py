# -*- encoding: utf-8 -*-
import json
import re
from pyzabbix import ZabbixAPI
from cmdbuild import CMDBuild


def main():
    cmdbuild = CMDBuild(ip='10.244.244.128', username='admin', password='3$rFvCdE', verbose=True)
    zabbix = ZabbixAPI(server="http://10.244.244.139/")
    zabbix.login('Admin', 'zabbix')
    for h in zabbix.host.get(output="extend"):
        description = re.findall(r".*(?=[:])", h['description'])[0]  # если после : дописан имя РТС
        filter = dict(name='Description', operator='LIKE', value=description)
        (json.dumps(cmdbuild.get_card_list('Hosts', _filter=filter), indent=2, ensure_ascii=False))
    (json.dumps(cmdbuild.get_card('zItems', 1391866), indent=2, ensure_ascii=False))
    (json.dumps(cmdbuild.get_card_list('zItems'), indent=2, ensure_ascii=False))
    (json.dumps(cmdbuild.get_card_history('zItems', 1391866), indent=2))
    (cmdbuild.create_card('AddressesIPv4', {'Address': '192.192.192.192/24'}))
    filter = dict(name='Address', operator='EQUALS', value='192.192.192.192/24')
    response = cmdbuild.get_card_list('AddressesIPv4', _filter=filter)
    for _id, v in response['Id'].items():
        (cmdbuild.update_card('AddressesIPv4', _id, {'Address': '192.192.192.192/24'}))
        (cmdbuild.delete_card('AddressesIPv4', _id))
if __name__ == '__main__':
    main()
