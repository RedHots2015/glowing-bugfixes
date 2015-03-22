#!/usr/bin/env python

from app import Mole, db
import sys


print('hello')

id = sys.argv[1]

# coding: utf-8

# In[35]:

import numpy as np
from skimage import io

# In[36]:

mole = Mole.query.filter(Mole.id == id).first()

image = io.imread('uploads/' + mole.filename)

mole.status = 10

db.session.merge(mole)
db.session.commit()

# In[37]:

from skimage.transform import rescale
small = rescale(image, 0.1)


# In[39]:

from skimage.color import rgb2gray
gray = rgb2gray(small)

# In[47]:

from skimage.feature import canny
edges = canny(gray, sigma=2)

mole.status = 15

db.session.merge(mole)
db.session.commit()

# In[48]:

from skimage.transform import hough_circle

hough_radii = np.arange(15, 30)
hough_res = hough_circle(edges, hough_radii)

mole.status = 45

db.session.merge(mole)
db.session.commit()

# In[122]:

from skimage.feature import peak_local_max
from skimage.draw import circle_perimeter
from skimage.color import gray2rgb

centers = []
accums = []
radii = []

for radius, h in zip(hough_radii, hough_res):
    # For each radius, extract two circles
    num_peaks = 2
    peaks = peak_local_max(h, num_peaks=num_peaks)
    centers.extend(peaks)
    accums.extend(h[peaks[:, 0], peaks[:, 1]])
    radii.extend([radius] * num_peaks)

coin_center = 0
coin_radius = 0
    
# Draw the most prominent 5 circles
gray_copy = gray2rgb(gray)
for idx in np.argsort(accums)[::-1][:1]:
    coin_center = centers[idx]
    coin_radius = radii[idx]

mole.status = 60

db.session.merge(mole)
db.session.commit()

# In[55]:

from skimage.exposure import equalize_hist

equal = equalize_hist(gray)

mole.status = 65

db.session.merge(mole)
db.session.commit()

# In[56]:

y,x = np.ogrid[:gray.shape[0],:gray.shape[1]]
cx = mole.mask_cx / 10
cy = mole.mask_cy / 10
radius = mole.mask_r / 10

r2 = (x-cx)*(x-cx) + (y-cy)*(y-cy)

mask = r2 <= radius * radius


# In[57]:

from skimage.feature import canny

mole_edge = canny(equal, sigma=2, mask=mask)

mole.status = 75

db.session.merge(mole)
db.session.commit()


# In[99]:

from skimage.measure import find_contours
contours = find_contours(mole_edge, 0.9, fully_connected='high')

mole.status = 85

db.session.merge(mole)
db.session.commit()


# In[64]:

from mahotas.polygon import fill_polygon
from skimage.transform import resize

canvas = np.zeros((gray.shape[0], gray.shape[1]))
fill_polygon(contours[0].astype(np.int), canvas)

mole.status = 95

db.session.merge(mole)
db.session.commit()



# In[78]:

import numpy.ma as ma
from skimage.color import rgb2hsv

hsv = rgb2hsv(small)

deviations = []
for color in (0,1,2):
    masked = ma.array(hsv[:,:,color], mask=~canvas.astype(np.bool))
    deviations.append(masked.std())
    
mole.h = deviations[0]
mole.s = deviations[1]
mole.v = deviations[2]

# In[104]:

from skimage.measure import CircleModel

circle_model = CircleModel()
circle_model.estimate(contours[0])
symmetry = circle_model.residuals(contours[0]).mean()

mole.symmetry = symmetry

# In[125]:

diameter = (19.05 / coin_radius) * (circle_model.params[2])

mole.diameter = diameter

mole.status = 100

db.session.merge(mole)
db.session.commit()
