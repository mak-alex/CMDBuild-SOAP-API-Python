# -*- encoding: utf-8 -*-
import json
from pyzabbix import ZabbixAPI
from cmdbuild import CMDBuild


def main():
    # Создаем новый инстанс с нужными параметрами
    cmdbuild = CMDBuild(ip='10.244.244.128', username='admin', password='3$rFvCdE')

    # Подберем дерево зависимостей для класса Hosts
    response = cmdbuild.get_card_list('Hosts')

if __name__ == '__main__':
    main()
