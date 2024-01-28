import os

from telebot import types
from random import randint
from roles import Student
import docx2pdf as dp
from datetime import datetime

class Files:
    available_formats = ('doc', 'docx', 'pdf')

    def __init__(self, file: bytes, extension: str):
        self._file = file

        try:
            self.path = os.path.abspath('../files/')
        except:
            raise Exception("no folder for files")
        os.chdir(self.path)

        if extension in self.available_formats:
            self.extension = extension
        else:
            raise Exception("invalid file format")

        self._name = 'file_' + str(randint(0, 10000))
        with open(self._name, "wb") as self.saving_file:
            self.saving_file.write(self._file)

        os.rename(self._name, self._get_filename_with_extension())
    def _get_filename_with_extension(self):
        return self.name + "." + self.extension
    @property
    def name(self):
        if hasattr(self, '_name'):
            return self._name
    @name.setter
    def name(self, name):
        now = datetime.now()
        filename_with_old_extension = self._get_filename_with_extension()
        if not str(datetime.now().year) in name:
            self._name = name + "_{}.{}.{}_{}.{}".format(now.day, now.month, now.year, now.hour, now.minute)
        else:
            self._name = name
        try:
            os.rename(filename_with_old_extension, self._get_filename_with_extension())
        except FileExistsError:
            os.remove(self._get_filename_with_extension())
            os.rename(filename_with_old_extension, self._get_filename_with_extension())

    def convert_to_pdf(self):
        if self.extension != 'pdf':
            filename_with_old_extension = self._get_filename_with_extension()
            self.extension = 'pdf'
            dp.convert(filename_with_old_extension, self._get_filename_with_extension())
    def get_src(self):
        return self.path.replace('\\', '/') + '/' + self._get_filename_with_extension()