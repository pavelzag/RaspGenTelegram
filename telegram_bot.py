import datetime
import json
import requests
import time
from logger import logging_handler
from send_mail import send_mail
from configuration import get_config
from dbconnector import get_gen_state, get_last_time_spent

from_address = 'yardeni.generator.dev@gmail.com'
TOKEN = get_config('creds', 'telegram_token')
white_list = get_config('creds', 'white_list')
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
telegram_success_msg = 'Message was received succesfully.'
telegram_failure_msg = 'Message was not received succesfully.'
global interrupt
interrupt = False


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
    return text, chat_id


def send_message(text, chat_id):
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)


def retry_db_status(i, db_status):
    print('{} {}'.format('DB Status is ', db_status))
    print('{} {}'.format('Attempt number ', i))
    time.sleep(5)
    return get_gen_state()


def check_command_executed(key_command):
    i = 1
    db_status = get_gen_state()
    if 'on' in key_command:
        while db_status != 'up' and i < 11:
            db_status = retry_db_status(i, db_status)
            i += 1
        else:
            print('{} {}'.format('DB Status is ', db_status))
            return True
    elif key_command == 'off':
        while db_status != 'down' and i < 11:
            db_status = retry_db_status(i, db_status)
            i += 1
        else:
            print('{} {}'.format('DB Status is ', db_status))
            return True
    elif key_command == 'status':
        return get_gen_state()


def wait_for_interrupt(run_time, interrupt):
    off_time = datetime.datetime.now() + datetime.timedelta(0, 0, 0, 0, run_time)
    last_update_id = None
    while off_time > datetime.datetime.now() and interrupt == False:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            key_command, chat_id = get_last_chat_id_and_text(updates)
            send_mail(send_to=from_address, subject=key_command)
            if key_command.lower() == 'off':
                interrupt = True
    if not interrupt:
        send_mail(send_to=from_address, subject='off')
        time_spent = ' '.join(get_last_time_spent())
        msg = '{} {} {}'.format(telegram_success_msg, 'Generator is going down. Generator was up for',
                                time_spent)
        send_message(msg, chat_id)
    return interrupt


def main():
    mail_sent = None
    chat_id = None
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            key_command, chat_id = get_last_chat_id_and_text(updates)
            if str(chat_id) not in white_list:
                msg = 'You are not allowed'
                send_message(msg, chat_id)
            elif str(chat_id) in white_list:
                key_command = key_command.lower()
                send_mail(send_to=from_address, subject=key_command)
                # time_spent = ' '.join(get_last_time_spent())
                if key_command == 'status':
                    msg = ('{} {}'.format('Generator status is:', get_gen_state()))
                    send_message(msg, chat_id)
                else:
                    if check_command_executed(key_command):
                        if 'on' in key_command:
                            if any(char.isdigit() for char in key_command):
                                timeout_frame = int(key_command.split("on", 1)[1])
                                msg = '{} {} {} {}'.format(telegram_success_msg,
                                                           'Generator is going up for', timeout_frame, 'minutes')
                            else:
                                msg = '{} {} {}'.format(telegram_success_msg, 'Generator is going', key_command)
                            mail_sent = False
                        else:
                            time_spent = ' '.join(get_last_time_spent())
                            msg = '{} {} {} {}'.format(telegram_success_msg, 'Generator was up for', time_spent, 'minutes')
                        if not mail_sent:
                            send_message(msg, chat_id)
                    else:
                        send_message(telegram_failure_msg, chat_id)
                if any(char.isdigit() for char in key_command):
                    timeout_frame = int(key_command.split("on", 1)[1])
                    interrupt_flag = wait_for_interrupt(timeout_frame, interrupt)
                    if interrupt_flag:
                        time_spent = ' '.join(get_last_time_spent())
                        msg = '{} {} {}'.format(telegram_success_msg, 'Generator is going down. Generator was up for',
                                                      time_spent)
                        send_message(msg, chat_id)
                        mail_sent = True
        time.sleep(0.5)


if __name__ == '__main__':
    main()
