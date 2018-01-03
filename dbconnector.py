import logging
from logger import logging_handler
from os import uname
import time
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


def calculate_time_span(time_span):
    """"Returns the time span in tuple format"""
    if time_span > 3600:
        return time.strftime("%H:%M:%S", time.gmtime(time_span)), 'hours'
    if time_span > 60:
        return time.strftime("%M:%S", time.gmtime(time_span)), 'minutes'
    else:
        return int(time_span), 'seconds'


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


def get_last_time_spent():
    # Some time out in order to get the latest record
    time.sleep(5)
    cursor = db.time_spent.find().sort([('time_stamp', -1)]).limit(1)
    for document in cursor:
        time_span = document['time_span']
        return calculate_time_span(time_span)


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
