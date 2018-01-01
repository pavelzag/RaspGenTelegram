import os.path
import yaml


def get_config(parameter_type, parameter_name):
    if 'DYNO' in os.environ:
        is_heroku = True
    else:
        is_heroku = False

    if is_heroku:
        return os.environ.get(parameter_name, 'Theres\'s nothing here')
    else:
        with open("config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        if parameter_type == 'creds':
            return cfg['creds'][parameter_name]
