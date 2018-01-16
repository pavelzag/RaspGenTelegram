import os.path
import yaml

if 'DYNO' in os.environ:
    is_heroku = True
else:
    is_heroku = False


def get_config(parameter_type, parameter_name):
    if is_heroku:
        return os.environ.get(parameter_name, 'Theres\'s nothing here')
    else:
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        if parameter_type == 'creds':
            return cfg['creds'][parameter_name]


def get_db_creds(parameter_type, parameter_name):
    if is_heroku:
        return os.environ.get(parameter_name, 'Theres\'s nothing here')
    else:
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        if parameter_type == 'creds':
            return cfg['creds'][parameter_name]
        elif parameter_type == 'mongodb':
            return cfg['mongodb'][parameter_name]


def get_cam_url(parameter_name):
    if is_heroku:
        return os.environ.get(parameter_name, 'Theres\'s nothing here')
    else:
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        return cfg['cam_url']