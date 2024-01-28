from fpdf import FPDF
from PIL import Image

pdf = FPDF()
pdf.add_page()
pdf.set_font("times", size=20, style='B')
images_path = ['photo_2024-01-24_18-31-04.jpg', 'photo_2024-01-26_15-16-10.jpg', 'photo_2024-01-26_15-16-14.jpg', 'tg_image_1565650556.jpeg', 'tg_image_2322871185.jpeg']
counter = 0
for path in images_path:
    counter += 1
    im = Image.open(path)
    w, h = im.size
    k = w // 180
    if k > 1:
        w //= k
        h //= k
    pdf.cell(50, 30, txt=f"#{counter}", ln=1, align="C")
    pdf.image(path, w=w, h=h)
pdf.output('simple_demo.pdf')