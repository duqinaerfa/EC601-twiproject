import os

os.popen('ffmpeg -r 0.5 -i img%03d.jpg -vf scale=500:500 -y -r 30 -t 60 out.mp4')
