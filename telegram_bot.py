import json
import requests
import time
from logger import logging_handler
from send_mail import send_mail
from configuration import get_config
from dbconnector import get_gen_state

from_address = 'yardeni.generator.dev@gmail.com'
TOKEN = get_config('creds', 'telegram_token')
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
telegram_success_msg = 'Message was received succesfully'
telegram_failure_msg = 'Message was not received succesfully'


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id):
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)


def retry_db_status(i, db_status):
    print('{} {}'.format('DB Status is ', db_status))
    print('{} {}'.format('Attempt number ', i))
    time.sleep(5)
    return get_gen_state()


def check_command_executed(command):
    i = 1
    db_status = get_gen_state()
    if command == 'on':
        while db_status != 'up' and i < 11:
            db_status = retry_db_status(i, db_status)
            i += 1
        else:
            print('{} {}'.format('DB Status is ', db_status))
            return True
    elif command == 'off':
        while db_status != 'down' and i < 11:
            db_status = retry_db_status(i, db_status)
            i += 1
        else:
            print('{} {}'.format('DB Status is ', db_status))
            return True
    elif command == 'status':
        return get_gen_state()


def main():
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            command, chat_id = get_last_chat_id_and_text(updates)
            send_mail(send_to=from_address, subject=command)
            if command == 'status':
                msg = ('{} {}'.format('Generator status is:', get_gen_state()))
                send_message(msg, chat_id)
            else:
                if check_command_executed(command):
                    send_message(telegram_success_msg, chat_id)
                else:
                    send_message(telegram_failure_msg, chat_id)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
