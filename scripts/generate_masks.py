from rembg import remove
from PIL import Image
import os
import io

inp = r"data\test_object\images"      # use ORIGINAL images
out_mask = r"data\test_object\masks"
os.makedirs(out_mask, exist_ok=True)

for f in os.listdir(inp):
    if not f.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    path = os.path.join(inp, f)

    with open(path, "rb") as i:
        result = remove(i.read())

    img = Image.open(io.BytesIO(result)).convert("RGBA")
    alpha = img.split()[-1]  # alpha channel

    base = os.path.splitext(f)[0]
    alpha.save(os.path.join(out_mask, base + ".png"))

print("Masks created.")