import json
from cmdbuild import CMDBuild as cmdbuild

t = cmdbuild(
    username='admin',
    password='3$rFvCdE',
    ip='10.244.244.128',
    verbose=True,
    debug=False
)

r = t.get_card_list('Hosts')
print(json.dumps(r, indent=2))

