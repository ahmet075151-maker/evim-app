# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw

SIZE = 512
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Arka plan - yuvarlatılmış kare, turuncu-lacivert gradyan hissi
bg_color = (255, 111, 60, 255)
d.rounded_rectangle([0, 0, SIZE, SIZE], radius=110, fill=bg_color)

# Ev gövdesi
body_color = (255, 255, 255, 255)
d.rounded_rectangle([140, 260, 372, 420], radius=16, fill=body_color)

# Çatı (üçgen)
roof_color = (255, 255, 255, 255)
d.polygon([(256, 110), (110, 270), (402, 270)], fill=roof_color)

# Baca
d.rectangle([320, 150, 355, 230], fill=roof_color)

# Kapı (arka plan rengiyle boşluk)
d.rectangle([232, 330, 280, 420], fill=bg_color)

# Pencere
d.rounded_rectangle([175, 300, 210, 335], radius=4, fill=bg_color)

img.save("icon.png")
print("icon.png oluşturuldu")
