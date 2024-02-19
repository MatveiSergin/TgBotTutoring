import os

from PIL import Image
from fpdf import FPDF
from telebot import types
from random import randint
from roles import Student
import docx2pdf as dp
from datetime import datetime
import subprocess
import sys
import json

# noinspection PyPackageRequirements
class File_faсtory:
    available_formats = ('doc', 'docx', 'pdf', 'zip')

    def __init__(self, file: bytes | FPDF, extension: str):
        self._file = file

        if extension in self.available_formats:
            self.extension = extension
        else:
            raise Exception("invalid file format")

        if not os.path.exists('files'):
            os.mkdir('files')

        self._name = 'file_' + str(randint(0, 10000))
        if isinstance(self._file, bytes):
            with open(os.path.join('files', self._name), "wb") as saving_file:
                saving_file.write(self._file)
            os.rename(os.path.join('files', self._name), os.path.join('files', self._get_filename_with_extension()))
        else:
            self._file.output(os.path.join('files', self._get_filename_with_extension()))

    def _get_filename_with_extension(self):
        return f"{self.name}.{self.extension}"
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
            os.rename(os.path.join('files', filename_with_old_extension), os.path.join('files', self._get_filename_with_extension()))
        except FileExistsError:
            os.remove(os.path.join('files', self._get_filename_with_extension()))
            os.rename(os.path.join('files', filename_with_old_extension), os.path.join('files', self._get_filename_with_extension()))

    def convert_to_pdf(self):

        if sys.platform == 'win32' and self.extension != 'pdf':
            filename_with_old_extension = self._get_filename_with_extension()
            self.extension = 'pdf'
            dp.convert(os.path.join('files', filename_with_old_extension), os.path.join('files', self._get_filename_with_extension()))
        elif self.extension != 'pdf':
            filename_with_old_extension = self._get_filename_with_extension()
            self.extension = 'pdf'
            subprocess.call(['soffice',
                             # '--headless',
                             '--convert-to',
                             'pdf',
                             '--outdir',
                             self._get_filename_with_extension(),
                             filename_with_old_extension])

    def __repr__(self):
        return os.path.join(os.getcwd(), 'files', self._get_filename_with_extension()).replace('\\', '/')



class HomeworkDocument():
    FONT_FAMILY = "times"
    FONT_SIZE = 20
    FONT_STYLE_BOLT = 'B'
    FONT_STYLE_ITALIC = 'C'
    WIDTH_IMAGE = 50
    HEIGHT_IMAGE = 30
    def __init__(self, *args):
        self._image_paths = args
        self._сounter_task = 0
        self._pdf = FPDF()
        self._pdf.add_page()
        self._pdf.set_font(self.FONT_FAMILY, size=self.FONT_SIZE, style=self.FONT_STYLE_BOLT)
        if self._image_paths:
            for path in self._image_paths:
                self.add_new_task(path)
    def add_new_task(self, path: str):

        self._сounter_task += 1
        im = Image.open(path)
        width, height = im.size
        ratio = width // 180
        if ratio > 1:
            width //= ratio
            height //= ratio
        self._pdf.cell(self.WIDTH_IMAGE, self.HEIGHT_IMAGE, txt=f"#{self._сounter_task}", ln=1, align=self.FONT_STYLE_ITALIC)
        self._pdf.image(path, w=width, h=height)

    def get_file(self):
        return File_faсtory(self._pdf, extension='pdf')

class Jpg_file:
    def __init__(self, file: bytes):
        if not os.path.isdir(os.path.join("files", "photos")):
            os.mkdir(os.path.join('files', "photos"))

        self.name = f"file{randint(0, 1000)}.jpg"
        with open(os.path.join('files', 'photos', self.name), "wb") as self.file_photo:
            self.file_photo.write(file)

    def __repr__(self):
        return os.path.join(os.getcwd(), 'files', 'photos', self.name).replace("\\", "/")

    def __del__(self):
        os.remove(repr(self))


class Callback_data:

    def __init__(self, name: str):
        self._items = {}
        self.name = name

    def add_value(self, key, value):
        if key not in self._items:
            self._items[key] = value
        else:
            raise Exception("key in dict yet")
    def add_item(self, item):
        if item[0] not in self._items:
            self._items |= dict((item, ))

    def add_items(self, *args: tuple):
        if not all(isinstance(item, tuple) for item in args):
            raise TypeError("args must be tuple")
            return
        for item in args:
            self.add_item(item)

    def get_value(self, key: str):
        if key in self._items:
            return self._items[key]

    def deleting_by_key(self, key):
        if key in self._items:
            del self._items[key]




