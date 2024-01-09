from configparser import SafeConfigParser
import os
class DBProperties:
    def __init__(self):
        self.file_name = os.path.abspath('../src/config/config.ini')

        f = open(self.file_name)
        f.close()
        self.cfgParser = SafeConfigParser()
        self.cfgParser.read(self.file_name)
    def get_host(self):
        return self.cfgParser.get('database', 'HOST')

    def get_port(self):
        return int(self.cfgParser.get('database', 'PORT'))

    def get_user(self):
        return self.cfgParser.get('database', 'USER')
    def get_password(self):
        return self.cfgParser.get('database', 'PASSWORD')
    def get_db_name(self):
        return self.cfgParser.get('database', 'DB_NAME')
