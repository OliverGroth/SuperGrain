# Classical segmentation of the grain boundary

import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy import ndimage
from skimage import morphology
from skimage import measure
from PIL import Image

# Import image
img = Image.open('img1.png')

channel0 = img[:, :, 0]
channel1 = img[:, :, 1]
channel2 = img[:, :, 2]

# Display the different channels
plt.figure(1)
plt.imshow(channel0, cmap='gray')
plt.title('Blue Channel of Original Image')
plt.axis('off')
plt.show()

plt.figure(2)
plt.imshow(channel1, cmap='gray')
plt.title('Blue Channel of Original Image')
plt.axis('off')
plt.show()

plt.figure(3)
plt.imshow(channel2, cmap='gray')
plt.title('Blue Channel of Original Image')
plt.axis('off')
plt.show()
