from configparser import RawConfigParser
import os
class DBProperties:
    _section = 'database'
    def __init__(self):
        self.file_name = os.path.abspath('../src/config/configDB.ini')
        self.cfgParser = RawConfigParser()
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
