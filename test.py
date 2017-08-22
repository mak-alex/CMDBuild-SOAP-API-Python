import json
from cmdbuild import CMDBuild as cmdbuild

t = cmdbuild(
    username='admin',
    password='3$rFvCdE',
    url='http://10.244.244.128/cmdbuild/services/soap/Webservices?wsdl',
    verbose=True,
    debug=False
)

h = t.get_card_list('Hosts')
print(json.dumps(h, indent=2, ensure_ascii=False, sort_keys=False))
i = t.get_card_list('zItems')
print(json.dumps(i, indent=2, ensure_ascii=False, sort_keys=False))
ione = t.get_card('zItems', 1391866)
print(json.dumps(ione, indent=2, ensure_ascii=False, sort_keys=False))
l = t.get_lookup_list('LOC_TYPE')
for i in l:
    print(t.get_lookup_by_id(i['id']))
