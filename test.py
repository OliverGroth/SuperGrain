# Testing preprocessing methods as described in:
# J Food Process Engineering - 2021 - Sun - Deep learning optimization method for counting overlapping rice seeds

# Import libraries
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load img1.png
input_image = cv2.imread("img1.png")

# Binarization
# Convert to grayscale
gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
# Apply Gaussian Blur
blur = cv2.GaussianBlur(gray, (5, 5), 0)
# Apply Otsu's thresholding
ret, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

# Display the binarized image
plt.figure(1)
plt.imshow(thresh, cmap='gray')
plt.title('Binarized Image')
plt.axis('off')
plt.show()

# Remove noise
# Remove small white noise
kernel = np.ones((3, 3), np.uint8)
# Remove small black holes
closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

# Display the noise-removed image
plt.figure(2)
plt.imshow(closing, cmap='gray')
plt.title('Noise-Removed Image')
plt.axis('off')
plt.show()
