# CMDBuild SOAP API Python Wrapper
![Alt text](http://www.cmdbuild.org/logo.png)![Alt text](https://www.python.org/static/opengraph-icon-200x200.png)

CMDBuild is an open source software to manage the configuration database (CMDB).
CMDBuild is compliant with ITIL "best practices" for the IT services management according to process-oriented criteria.

###CMDBuild Webservice Manual:
	 http://www.cmdbuild.org/file/manuali/webservice-manual-in-english
   
###Dependencies
 - suds
   
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
      get_lookup_list_by_code(self, lookup_type, lookup_code, parent_list)
      get_lookup_by_id(self, lookup_id)
      create_relation(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date)
      create_relation_with_attributes(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date, attributes_list)
      delete_relation(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date)
      get_relation_list(self, domain, classname, card_id)
      get_relation_list_ext(self, domain, classname, card_id)
      get_relation_history(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date)
      get_relation_attributes(self, domain_name, class_1_name, card_1_id, class_2_name, card_2_id, status, begin_date, end_date)
      start_workflow(self, class_name, card_id, attributes_list, begin_date, user, complete_task)
      update_workflow(self, class_name, card_id, attributes_list, begin_date, user, complete_task)
      resume_workflow(self, class_name, card_id, attributes_list, begin_date, user, complete_task)
      get_reference(self, classname, query, order_type, limit, offset, full_text_query)
      get_attachment_list(self, classname, card_id=None)
      upload_attachment(self, class_name, object_id, _file, filename, category, description)
      download_attachment(self, classname, object_id, filename)
      delete_attachment(self, classname, card_id, filename)
      update_attachment_description(self, classname, card_id, filename, description)
      get_activity_menu_schema(self)
      get_activity_objects(self, classname, card_id)
      get_attribute_list(self, classname)
      get_menu_schema(self)
      get_card_menu_schema(self)
      get_process_help(self, classname, card_id)
```

###Usage
```python
from cmdbuild import CMDBuild as cmdbuild

t = cmdbuild(
    username='user',
    password='pass',
    url='http://localhosts/cmdbuild/services/soap/Webservices?wsdl',
    verbose=True,
    debug=False
)

hosts = t.get_card_list('Hosts')
print(hosts)
# one_item = t.get_card('zItems', 1391866)
# print(one_item)
# lookups = t.get_lookup_list('LOC_TYPE')
# for lookup in lookups:
#    print(t.get_lookup_by_id(lookup['id']))
```

##### P.S. Test version. When I have time, working on it.

#### Please report error with the hashtag **#cmdbuild_soap_api_python** to the mail <alex-m.a.k@yandex.kz>

