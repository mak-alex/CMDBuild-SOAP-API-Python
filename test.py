# -*- encoding: utf-8 -*-
import json
from pyzabbix import ZabbixAPI
from cmdbuild import CMDBuild


def main():
    cmdbuild = CMDBuild(ip='10.244.244.128', username='admin', password='3$rFvCdE')
    zabbix = ZabbixAPI(server="http://10.244.244.139/")
    zabbix.login('Admin', 'zabbix')
    for h in zabbix.host.get(output="extend"):
        print(json.dumps(h, indent=2, ensure_ascii=False))
        filter = dict(name='Description', operator='EQUALS', value=h['description'])
        print(json.dumps(cmdbuild.get_card_list('Hosts', _filter=filter), indent=2, ensure_ascii=False))
if __name__ == '__main__':
    main()
