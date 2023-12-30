class Singl(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singl, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Test(metaclass=Singl):

    def conn(self, str):
        print(str)

Test().conn("123")