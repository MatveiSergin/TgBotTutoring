from configparser import SafeConfigParser
import os
TOKEN = '6663442009:AAG_5Z2PmhvtGjR6H-H-VibOlsVcI2lT8ZQ'

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TelebotProperties(metaclass=Singleton):
    cfgParser = None
    _section = 'telebot'
    def __init__(self):
        if self.cfgParser is None:
            file_name = os.path.abspath('../src/config/config_telebot.ini')
            self.cfgParser = SafeConfigParser()
            self.cfgParser.read(file_name)
    def get_token(self):
        return self.cfgParser.get(self._section, 'token')


class DBProperties(metaclass=Singleton):
    cfgParser = None
    _section = 'database'
    instance = None
    def __init__(self):
        if self.cfgParser is None:
            self.file_name = os.path.abspath('../src/config/configDB.ini')
            self.cfgParser = SafeConfigParser()
            self.cfgParser.read(self.file_name)

    def get_host(self):
        return self.cfgParser.get(self._section, 'HOST')

    def get_port(self):
        return int(self.cfgParser.get(self._section, 'PORT'))

    def get_user(self):
        return self.cfgParser.get(self._section, 'USER')

    def get_password(self):
        return self.cfgParser.get(self._section, 'PASSWORD')

    def get_db_name(self):
        return self.cfgParser.get(self._section, 'DB_NAME')