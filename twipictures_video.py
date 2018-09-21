import os
import io

os.popen('ffmpeg -r 0.5 -i img%03d.jpg -vf scale=500:500 -y -r 30 -t 60 out.mp4')

from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw, ImageFont

# Instantiates a client
client = vision.ImageAnnotatorClient()

path = './'
filelist = os.listdir(path)
total_num = len(filelist)

for file in filelist:
    if file.endswith('.jpg'):
        with io.open(file, 'rb') as image_file:
            content = image_file.read()

        image = types.Image(content=content)

        response = client.label_detection(image=image)
        labels = response.label_annotations

        # Add label to image
        img = Image.open(file)
        draw = ImageDraw.Draw(img)

        # print(file)
        # print('Labels:')
        labelword = ''
        for label in labels:
            labelword += str(label.description)+'\n'

        # print(labelword)
        (w, h) = img.size
        ttfont = ImageFont.truetype("/Library/Fonts/Arial.ttf", 30)
        draw.text((w/2-100, h/2-100), labelword, fill=(255, 255, 255), font=ttfont)
        img.save(file)
