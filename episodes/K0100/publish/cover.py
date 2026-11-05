import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, out, num, l1, l2 = sys.argv[1:6]
F = "assets/fonts/NotoSansTamil-ExtraBold.ttf"
im = Image.open(src).convert("RGB")
w, h = im.size; s = max(1080 / w, 1920 / h)
im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
x0, y0 = (im.width - 1080) // 2, (im.height - 1920) // 2
im = im.crop((x0, y0, x0 + 1080, y0 + 1920)).convert("RGBA")
# soft dark wash behind the title so it reads on a bright sky
wash = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(wash)
for y in range(0, 700):
    d.line([(0, y), (1080, y)], fill=(0, 0, 0, int(150 * max(0, 1 - y / 700))))
im = Image.alpha_composite(im, wash); d = ImageDraw.Draw(im)
L = ImageFont.Layout.RAQM
pill_f = ImageFont.truetype(F, 64, layout_engine=L)
tw = d.textlength(num, font=pill_f)
d.rounded_rectangle([540 - tw / 2 - 40, 180, 540 + tw / 2 + 40, 280], 55, fill=(214, 40, 40, 255))
d.text((540, 230), num, font=pill_f, anchor="mm", fill="white")
for text, y, size, col in [(l1, 385, 140, (255, 214, 64)), (l2, 515, 120, "white")]:
    f = ImageFont.truetype(F, size, layout_engine=L)
    while d.textlength(text, font=f) > 980:
        size -= 6; f = ImageFont.truetype(F, size, layout_engine=L)
    d.text((540, y), text, font=f, anchor="mm", fill=col, stroke_width=8, stroke_fill="black")
logo = Image.open("assets/brand/logo_badge.png").convert("RGBA"); logo.thumbnail((190, 190))
im.alpha_composite(logo, (1080 - logo.width - 40, 1920 - logo.height - 60))
im.convert("RGB").save(out, quality=92)
