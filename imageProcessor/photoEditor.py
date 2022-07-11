from PIL import Image, ImageEnhance, ImageFilter
import os

path = "./imgs" # folder for unedited images
pathOut = "./editedImgs" # folder for edited images

for filename in os.listdir(path):
    img = Image.open(f"{path}/{filename}")

    # sharpening, BW
    edit = img.filter(ImageFilter.SHARPEN).convert('L').rotate(-90)

    # contrast
    factor = 1.5
    enhancer = ImageEnhance.Contrast(edit)
    edit = enhancer.enhance(factor)

    # ADD MORE EDITS FROM DOCUMENTATION https://pillow.readthedocs.io/en/stable/

    clean_name = os.path.splitext(filename)[0]

    edit.save(f'.{pathOut}/{clean_name}_edited.jpg')
