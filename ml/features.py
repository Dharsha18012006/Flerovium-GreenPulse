"""Original fixed color/texture descriptor; no learned or pretrained image encoder."""
import numpy as np
from PIL import Image

def extract(image):
    im=image.convert('RGB').resize((96,96))
    rgb=np.asarray(im,dtype=np.float32)/255
    hsv=np.asarray(im.convert('HSV'),dtype=np.float32)/255
    gray=np.asarray(im.convert('L'),dtype=np.float32)/255
    features=[]
    for array in [rgb,hsv]:
        for channel in range(3):
            hist,_=np.histogram(array[:,:,channel],bins=16,range=(0,1))
            features.extend(hist/hist.sum())
        for y in range(0,96,24):
            for x in range(0,96,24):
                patch=array[y:y+24,x:x+24]
                features.extend(patch.mean(axis=(0,1)))
                features.extend(patch.std(axis=(0,1)))
    center=gray[1:-1,1:-1];code=np.zeros(center.shape,dtype=np.uint8)
    for bit,(dy,dx) in enumerate([(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1)]):
        code|=((gray[1+dy:95+dy,1+dx:95+dx]>=center).astype(np.uint8)<<bit)
    hist=np.bincount(code.ravel(),minlength=256);features.extend(hist/hist.sum())
    gy,gx=np.gradient(gray);magnitude=np.hypot(gx,gy);angle=(np.arctan2(gy,gx)+np.pi)/(2*np.pi)
    hist,_=np.histogram(angle,bins=16,range=(0,1),weights=magnitude)
    features.extend(hist/(hist.sum()+1e-8))
    return np.asarray(features,dtype=np.float32)
