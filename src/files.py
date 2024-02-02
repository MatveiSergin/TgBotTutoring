import os

from PIL import Image
from fpdf import FPDF
from telebot import types
from random import randint
from roles import Student
import docx2pdf as dp
from datetime import datetime

class File_faсtory:
    available_formats = ('doc', 'docx', 'pdf')

    def __init__(self, file: bytes | FPDF, extension: str):
        self._file = file
        try:
            if os.getcwd().split("\\")[-1] == "src":
                os.chdir(os.path.abspath('../files/'))
            elif os.getcwd().split("\\")[-1] == "photos":
                os.chdir(os.path.abspath('../'))
            self.path = os.getcwd()
        except:
            raise Exception("no folder for files")
        os.chdir(self.path)

        if extension in self.available_formats:
            self.extension = extension
        else:
            raise Exception("invalid file format")

        self._name = 'file_' + str(randint(0, 10000))
        if isinstance(self._file, bytes):
            with open(self._name, "wb") as self.saving_file:
                self.saving_file.write(self._file)
                os.rename(self._name, self._get_filename_with_extension())
        else:
            self._file.output(self._get_filename_with_extension())

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
    def __repr__(self):
        return self.path.replace('\\', '/') + '/' + self._get_filename_with_extension()



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
        if os.getcwd().split("\\")[-1] == "src":
            os.chdir(os.path.abspath('../files/photos/'))
        elif os.getcwd().split("\\")[-1] == "files":
            os.chdir('photos')
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
        if os.getcwd().split("\\")[-1] == "src":
            os.chdir(os.path.abspath('../files/'))
            if not os.path.isdir("photos"):
                os.mkdir("photos")
            os.chdir("photos")
            self.path = os.getcwd()
        else:
            self.path = os.getcwd()
        self.name = f"file{randint(0, 1000)}.jpg"
        with open(self.name, "wb") as self.file_photo:
            self.file_photo.write(file)

    def __repr__(self):
        return self.path + "\\" + self.name

    def __del__(self):
        os.remove(repr(self))


