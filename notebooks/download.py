import youtube_dl

with open('data/unbalanced_train_segments.csv') as f:
    lines = f.readlines()

dl_list = [line.strip().split(',')[0].strip() for line in lines[3:]]

# opts = {
#     'format': 'best'
# }
# with youtube_dl.YoutubeDL(opts) as ydl:
#     ydl.download(['https://www.youtube.com/watch?v={}'.format(dl) for dl in dl_list[:5]])

import pafy

url = "https://www.youtube.com/watch?v={}".format('---1_cCGK4M')
video = pafy.new(url)

best = video.getbest()
best.download()

bestaudio = video.getbestaudio()
bestaudio.download()


import numpy as np
import cv2

cap = cv2.VideoCapture('[1333] D19E-948 kéo SE8 (19.01.2014) [HD1080].mp4')

while(cap.isOpened()):
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow('frame',gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

import soundfile as sf
data, samplerate = sf.read('audio.flac')
