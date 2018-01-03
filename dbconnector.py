import logging
from logger import logging_handler
from os import uname
from pymongo import MongoClient, errors
from configuration import get_db_creds, get_config

env = get_db_creds('mongodb', 'env')
test_uri = get_db_creds('mongodb','test_uri')
prod_uri = get_db_creds('mongodb', 'prod_uri')


if env == 'test':
    client = MongoClient(test_uri)
    db = client.raspgen_test
else:
    client = MongoClient(prod_uri)
    db = client.raspgen
print(db)


def get_gen_state():
    """"Gets generator's status"""
    msg = 'Getting generator status'
    logging_handler(msg)
    cursor = db.generator_state.find({})
    for document in cursor:
        if document['state'] is False:
            gen_state = 'down'
        else:
            gen_state = 'up'
        msg = '{} {}'.format('Generator status is:', gen_state)
        logging_handler(msg)
        return str(gen_state)



def get_time_spent(month):
    """"Gets generator's time spent on in seconds"""
    time_sum_seconds =[]
    cursor = db.time_spent.find({})
    for document in cursor:
        if month == document['time_stamp'].month:
            time_sum_seconds.append(document['time_span'])
    return sum(time_sum_seconds)


def set_time_spent(time_stamp, time_span):
    """"Sets generator's time spent on"""
    db.time_spent.insert_one({"time_stamp": time_stamp, "time_span": time_span})
