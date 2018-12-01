import twidatabase

testapi = twidatabase.myApi()

testapi.connect()

testapi.getimages()

testapi.label()

kw = 'singer'
results = testapi.mysql_search_label(kw)
print('mysql: these twiter account owns keyword {}:'.format(kw))
for r in results:
    print(r)

kw = 'microphone'
results = testapi.mongo_search_label(kw)
print('mongodb: these twiter account owns keyword {}:'.format(kw))
for r in results:
    print(r)

# print the total number of logs in the mysql database
log_num = testapi.mysql_total_log()
print('there are', log_num, 'logs in the mysql db')

# print the total number of logs in the mongodb
log_num = testapi.mongo_total_log()
print('there are', log_num, 'logs in the mongodb')