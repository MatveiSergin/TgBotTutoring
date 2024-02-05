import os

print(os.getcwd())

if not os.path.exists('files'):
    os.mkdir('files')

name = 'file_123'
print(os.getcwd())

with open(os.path.join('files', name), 'wb') as file:
    pass
os.rename(os.path.join('files', name), os.path.join('files', name) + ".pdf")
