from configparser import SafeConfigParser

class DBProperties:
    def __init__(self):
        self.file_name = "config/config.conf"
        self.cfgParser = SafeConfigParser()
        self.load()
    def load(self):
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
