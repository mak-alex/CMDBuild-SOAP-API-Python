# CMDBuild SOAP API Python Wrapper
![Alt text](http://www.cmdbuild.org/logo.png)![Alt text](https://www.python.org/static/opengraph-icon-200x200.png)

CMDBuild is an open source software to manage the configuration database (CMDB).
CMDBuild is compliant with ITIL "best practices" for the IT services management according to process-oriented criteria.

###CMDBuild Webservice Manual:
	 http://www.cmdbuild.org/file/manuali/webservice-manual-in-english
   
###Dependencies
	suds
   
###Install
	easy_install cmdbuild-soap-api
#####or 
	easy_install suds && git clone --depth=1 https://bitbucket.org/enlab/cmdbuild_soap_api_python cmdbuild
   
```python
    class CMDBuild
      __init__(self, username=None, password=None, url=None, verbose=False, debug=False)
      auth(self, username=None, password=None)
      get_card(self, classname, card_id, attributes_list=None)
      get_card_history(self, classname, card_id, limit=None, offset=None)
      get_card_list(self, classname, attributes_list=None, _filter=None, filter_sq_operator=None, order_type=None, limit=None, offset=None, full_text_query=None, cql_query=None, cql_query_parameters=None)
      delete_card(self, classname, card_id)
      create_card(self, classname, attributes_list, metadata=None)
      update_card(self, classname, card_id, attributes_list, metadata=None, begin_date=None)
      create_lookup(self, lookup_type, code, description, lookup_id=None, notes=None, parent_id=None, position=None)
      delete_lookup(self, lookup_id)
      update_lookup(self, lookup_type, code, description, lookup_id=None, notes=None, parent_id=None, position=None)
      get_lookup_list(self, lookup_type=None, value=None, parent_list=None)
      get_lookup_by_id(self, lookup_id)
      create_relation(self)
      delete_relation(self)
      get_relation_list(self, domain, classname, card_id)
      get_relation_history(self)
      start_workflow(self)
      update_workflow(self)
      upload_attachment(self)
      download_attachment(self)
      delete_attachment(self)
      update_attachment(self)
      get_menu_schema(self)
      get_card_menu_schema(self)
```

###Usage
```python
import json
from cmdbuild import CMDBuild as cmdbuild

t = cmdbuild(
    username='user',
    password='pass',
    url='http://localhosts/cmdbuild/services/soap/Webservices?wsdl',
    verbose=True,
    debug=False
)

hosts = t.get_card_list('Hosts')
print(json.dumps(hosts, indent=2, ensure_ascii=False, sort_keys=False))
# one_item = t.get_card('zItems', 1391866)
# print(json.dumps(one_item, indent=2, ensure_ascii=False, sort_keys=False))
# lookups = t.get_lookup_list('LOC_TYPE')
# for lookup in lookups:
#    print(t.get_lookup_by_id(lookup['id']))
```

##### P.S. Test version. When I have time, working on it.

#### Please report error with the hashtag **#cmdbuild_soap_api_python** to the mail <alex-m.a.k@yandex.kz>

