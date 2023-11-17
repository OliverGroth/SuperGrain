# Code to synthesize seed images

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import hashlib
import struct
from PIL import Image
import random

def read_seed(start_byte,out_hex):
    """
    This function reads the coordinates and some attributes of __one__  seed in an image from a .tbin file generated by
    SmartGrain.

    Inputs:
        start_byte: The first byte to start reading for the current seed
        out_hex: The full raw hexadecimal file, containing all seeds.
    Output:
        seed: a dictionary containing the fields
        ["Centroid", "IS (intersection?)", "Length", "width", "Area", "PL", "Circularity", "Contour"]
        , where Contour contains the coordinates of the pixels at the contour of the seed.
        new_start: The byte to start reading the next seed.
    """
    vals = []
    line = out_hex[start_byte:start_byte+48]
    for i in range(len(line) // 4):
        hexval = "".join(line[i * 4:i * 4 + 4][::-1])
        decimal_val = struct.unpack("!l", bytes.fromhex(hexval))[0]
        vals.append(decimal_val)

    vals2 = np.reshape(vals, [6, 2])
    # Bytes 48 through  52 are zeroes.

    # Next are a bunch of properties of the seed as computed by SmartGrain, described below, and stored in attrib.
    # Attributes = ["Centroid", "IS (intersection?)", "Length", "width", "Area", "PL", "Circularity"]
    line = out_hex[start_byte+52:start_byte+52+100]
    attrib = []
    for i in range(len(line) // 8):
        hexval = "".join(line[i * 8:i * 8 + 8][::-1])
        decimal_val = struct.unpack("!d", bytes.fromhex(hexval))[0]
        attrib.append(decimal_val)

    # Read the number of points defining the outline of the seed.
    line = out_hex[start_byte+304:start_byte+308]
    for i in range(len(line) // 4):
        hexval = "".join(line[i * 4:i * 4 + 4][::-1])
        decimal_val = struct.unpack("!l", bytes.fromhex(hexval))[0]
        n_points = decimal_val

    # Read the coordinate of the seeds.
    line = out_hex[start_byte+308:start_byte+308 + ((n_points ) * 3 * 4)]
    coords = []
    for i in range((n_points) * 3):
        hexval = "".join(line[i * 4:i * 4 + 4][::-1])
        decimal_val = struct.unpack("!l", bytes.fromhex(hexval))[0]
        coords.append(decimal_val)

    coords2 = np.reshape(coords, [n_points, 3])

    # Compute at which byte to start reading the next seed in the image.
    new_start = start_byte+308 + ((n_points ) * 3 * 4)

    # Store the seed attributes as a dictionary.
    seed = {}
    seed["Centroid"] = np.array([attrib[0], attrib[1]])
    seed["Intersection"] = np.array([attrib[2], attrib[3]])
    seed["Length"] = np.array([attrib[4]])
    seed["Width"] = np.array([attrib[5]])
    seed["Area"] = np.array([attrib[6]])
    seed["PL"] = np.array([attrib[7]])
    seed["Circularity"] = np.array([attrib[8]])
    seed["Contour"] = coords2

    return  seed, new_start

def segment_seeds(file, image):

    # Given a filename, start reading the data for all the seeds.
    # This is probably an ugly solution programming-wise, but it works. It keeps reading seeds from the tbin file, until the
    # new starting byte has reached end-of-file, without knowing how large the file is.
    seeds = []
    start_byte = 120
    i = 0
    try:

        # Read the entire hex-file.
        with open(file, "rb") as f:
            buff = f.read()
        out_hex = ['{:02X}'.format(b) for b in buff]

        #Keep reading the data for each seed in the image, until we reach the end.
        # Store them as a list of dictionaries, one for each seed.
        while True: # (don't do this hehe... can probably do something more elegant/smarter)
            seed, start_byte = read_seed(start_byte = start_byte, out_hex = out_hex)
            seeds.append(seed)
            i +=1
            print(f"Read seed no. {i}")
    except:
        print("ERROR")

    #plt.figure()
    areas = []
    Circularities = []
    areas = []

    for seed in seeds:
        #plt.plot(seed["Contour"][:,0],seed["Contour"][:,1],'b')
        #plt.plot(seed["Centroid"][0], seed["Centroid"][1], 'r.')

        inds = np.where(seed["Contour"][:,2] == 3)
        #plt.plot(seed["Contour"][inds,0][0],seed["Contour"][inds,1][0],'r')
        areas.append(seed["Area"])
        Circularities.append(seed["Circularity"])
    #plt.title("This looks weird, right? part of the ruler is segmented. See comment in code.")

    areas = np.array(areas)

    # Without being careful, SmartGrain can also segment other stuff, e.g., parts of the ruler, or tiny specks
    # which shouldn't be considered seeds. The below line removes unreasonably large, and small values.
    #  Real seeds seems to, __in this particular camera setup__, have reasonable seed areas vary between around 2000 - 5000
    seed_inds = np.where(np.all(np.hstack([np.array(areas) < 100000,  np.array(areas) > 200]), axis = 1))[0]
    real_seeds = [seeds[i] for i in seed_inds]

    return real_seeds

def create_mask(image, seeds):
    # Create a mask image, where the seeds are marked with white pixels.
    mask = np.zeros((image.shape[0], image.shape[1]))
    for seed in seeds:
        mask[seed["Contour"][:,1], seed["Contour"][:,0]] = 255
        # Fill in the seeds with white pixels
        cv2.fillPoly(mask, pts=[seed["Contour"][:,0:2]], color=(255,255,255))
        # Convert to 8-bit 1-channel image
        mask = mask.astype(np.uint8)

    # Enlarge the mask a bit

    kernel_size = 50
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    
    return mask, dilated_mask


def extract_background(image, mask):
    """
    Extracts the background from the image by inpainting the areas covered by seeds.

    :param image_path: Path to the original image.
    :param mask_path: Path to the mask image where seeds are marked.
    :return: Image with seeds removed.
    """

    # Show image with masked seeds
    plt.figure()
    plt.imshow(image)
    plt.show()

    plt.figure()
    plt.imshow(mask)
    plt.show()


    # Now create a background image by inpainting the masked image and replacing the masked seeds with background
    background = cv2.inpaint(image, mask, 30, cv2.INPAINT_TELEA)

    return background


def check_overlap():
    """
    Check if a seed overlaps with any of the seeds already placed on the background.
    """
    pass

def place_seeds(background, image, mask, max_overlap, border):
    """ 
    Place seeds on the background with random position and rotation. 
    """
    h, w = background.shape[:2]

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    seeds = []
    for contour in contours:
        # Create a mask for the current contour
        contour_mask = np.zeros_like(mask)
        cv2.drawContours(contour_mask, [contour], -1, (255), thickness=cv2.FILLED)

        # Apply the mask to extract the seed
        seed = cv2.bitwise_and(image, image, mask=contour_mask)
        seeds.append((seed, contour_mask))

    for seed in seeds:
        
        seed_image, mask = seed

        # Find the center of the seed for rotation
        M = cv2.moments(mask)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = mask.shape[1] // 2, mask.shape[0] // 2

        # Random rotation
        angle = random.randint(0, 360)
        rotation_matrix = cv2.getRotationMatrix2D((cX, cY), angle, 1)
        rotated_seed = cv2.warpAffine(seed_image, rotation_matrix, (mask.shape[1], mask.shape[0]))
        rotated_mask = cv2.warpAffine(mask, rotation_matrix, (mask.shape[1], mask.shape[0]))


        # Random position
        max_x, max_y = background.shape[1] - mask.shape[1], background.shape[0] - mask.shape[0]
        rand_x, rand_y = random.randint(0, max_x), random.randint(0, max_y)

        print(rand_x, rand_y)

        # Create a region to place the seed
        background_region = background[rand_y:rand_y+mask.shape[0], rand_x:rand_x+mask.shape[1]]
        


        # Place the rotated seed on the background
        seed_placed = cv2.bitwise_and(background_region, background_region, mask=cv2.bitwise_not(rotated_mask))
        seed_placed = cv2.add(seed_placed, cv2.bitwise_and(rotated_seed, rotated_seed, mask=rotated_mask))
        background[rand_y:rand_y+mask.shape[0], rand_x:rand_x+mask.shape[1]] = seed_placed

    return background, mask

def main():
    file = "$$IMG_9291.tbin"
    image = Image.open("IMG_9291.JPG")
    image = cv2.imread("IMG_9291.JPG")

    seeds = segment_seeds(file, image)
    mask, dilated_mask = create_mask(image, seeds)
    #background = extract_background(image, dilated_mask)
    background = cv2.imread("background.jpg")
    
    new_image, mask = place_seeds(background, image, mask, max_overlap=0.1, border=100)
    

    plt.figure()
    plt.imshow(new_image)
    plt.show()

    # Save new_image
    cv2.imwrite("new_image.jpg", new_image)

    return


if __name__ == "__main__":
    main()
