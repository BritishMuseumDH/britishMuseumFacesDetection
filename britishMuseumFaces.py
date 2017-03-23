#!/usr/bin/env python
from __future__ import print_function

## Retrieve images from British Museum Research Space and perform montage and facial recognition
## Daniel Pett 21/3/2017
## British Museum content is under a CC-BY-SA-NC license
__author__ = 'portableant'
__license__ = 'CC-BY'
## Tested on Python 2.7.13
## You will need to download the opencv file haarcascade_frontalface_default.xml for the facial bit to work and place
## this in opencv folder

from SPARQLWrapper import SPARQLWrapper, JSON
import urllib
import os
from PIL import Image
import subprocess
import cv2
import argparse
import time

def make_executable(path):
    """
    Make the file executable
    :param path:
    :return:
    """
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)

# Function defined for resize and crop of an image
def resize_and_crop(img_path, modified_path, size, crop_type='top'):
    """
    Resize and crop an image to fit the specified size.
    args:
        img_path: path for the image to resize.
        modified_path: path to store the modified image.
        size: (width, height) tuple. Eg (300,300)
        crop_type: can be 'top', 'middle' or 'bottom'
    raises:
        Exception: if can not open the file in img_path of there is problems
            to save the image.
        ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], size[0] * img.size[1] / img.size[0]),
                Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, (img.size[1] - size[1]) / 2, img.size[0], (img.size[1] + size[1]) / 2)
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else :
            raise ValueError('Error detected: That option is not valid for crop type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((size[1] * img.size[0] / img.size[1], size[1]),
                Image.ANTIALIAS)
        # Switch for where to crops
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = ((img.size[0] - size[0]) / 2, 0, (img.size[0] + size[0]) / 2, img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else :
            raise ValueError('Error detected: That option is not valid for crop type')
        img = img.crop(box)
    else :
        img = img.resize((size[0], size[1]),
                Image.ANTIALIAS)
    img.save(modified_path)

def count_files( path, extension ):
    list_dir = []
    list_dir = os.listdir(path)
    count = 0
    for fn in list_dir:
        if fn.endswith(extension):  # eg: '.txt'
            count += 1
    return count

def create_montage( fn ):
    """
    Create the montage if file exists with a try catch block
    :param file:
    :return:
    """
    if os.path.isfile(fn):
        print("File exists")
        try:
            # Make sure you are in correct directory
            # This will produce multiple tiles for large results
            # Make sure you are in correct directory
            make_executable(fn)
            #time.sleep(5)
            subprocess.call("montage -border 0 -geometry 660x -tile 10x10 @" + os.path.basename(fn) + " montages/bmPortraitBusts.jpg", shell=True)
            # This call makes a montage of the faces detected
            subprocess.call("montage -border 0 -geometry 660x -tile " + dims + " facesDetected/* montages/bmPortraitBustsFaces.jpg", shell=True)
        except:
            # The process failed
            raise ValueError("Montage generation failed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A script for retrieving images from British Museum Research Space and '
                                             'perform montage and facial recognition')

    parser.add_argument('-p', '--path', help='The path in which to run this script', required=True)
    # An example would be: --path '/Users/danielpett/githubProjects/scripts/'

    # Parse arguments
    args = parser.parse_args()

    # Change this to your script path
    basePath = args.path

    # Define the base directories
    paths = {x: os.path.join(basePath, x) for x in ['bmimages', 'bmimagesResized', 'montages', 'facesDetected', 'opencv']}

    # Create them if they don't already exist
    for path in paths.values():
        if not os.path.exists(path):
            os.makedirs(path)

    # Set up your sparql endpoint
    sparql = SPARQLWrapper("http://collection.britishmuseum.org/sparql")

    # Set your query
    sparql.setQuery("""PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX crm: <http://erlangen-crm.org/current/>
PREFIX fts: <http://www.ontotext.com/owlim/fts#>
PREFIX bmo: <http://collection.britishmuseum.org/id/ontology/>

SELECT DISTINCT ?image
WHERE {
  ?object bmo:PX_object_type ?object_type .
  ?object_type skos:prefLabel "bust" .
  ?object bmo:PX_has_main_representation ?image .
} LIMIT 100""")

    # Return the JSON triples
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # Open the file for writing urls (this is for image magick)
    listImages = open(os.path.join(paths['bmimagesResized'], "files.txt"), 'w')


    # Iterate over the results
    for result in results["results"]["bindings"]:
        image = result["image"]["value"]
        if os.path.isfile(os.path.join(paths['bmimages'], os.path.basename(image))):
            print("File already exists")
        else:
            path = os.path.join(paths['bmimages'], os.path.basename(image))
            urllib.urlretrieve(image, path)
            print("Image " + os.path.basename(image) + " downloaded")

    for fn in os.listdir(paths['bmimages']):
        if not fn.startswith('.'):
            listImages.write(os.path.join(paths["bmimagesResized"], os.path.basename(fn)) + "\n")

    # Iterate through files and crop as required
    for fn in os.listdir(paths['bmimages']):
        # Make sure file is not a hidden one etc
        if not fn.startswith('.') and os.path.isfile(os.path.join(paths['bmimages'], fn)):
            # Open the file checking if it is valid or not. It fails otherwise :-(
            try:
                if not os.path.exists(os.path.join(paths['bmimagesResized'], fn)):
                    resize_and_crop(os.path.join(paths['bmimages'], fn), os.path.join(paths['bmimagesResized'], fn), (300, 300))
                    print(fn + " resized")
                else:
                    print("Resized file exists")
            except:
                pass

    # Amended to be relevant to the base path?
    cascPath = os.path.join(paths["opencv"], "haarcascade_frontalface_default.xml")
    # Check you have this file, if not get it
    if not os.path.isfile(cascPath):
        haar = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        urllib.urlretrieve(haar, cascPath)

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)
    start = time.time()
    for fn in os.listdir(paths['bmimages']):
        if not fn.startswith('.'):
            start = time.time()
            print("Detecting faces in " + os.path.join(paths['bmimages'], fn))
            image = cv2.imread(os.path.join(paths['bmimages'], fn))

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(150, 150),
                flags=cv2.CASCADE_SCALE_IMAGE
            )

            left = 10
            right = 10
            top = 10
            bottom = 10
            if(len(faces) > 0):
                for (x, y, w, h) in faces:
                    image  = image[y-top:y+h+bottom, x-left:x+w+right]
                    filename = os.path.join(paths["facesDetected"], "cropped_{1}_{0}".format(str(fn),str(x)))
                    if not os.path.exists(filename):
                        cv2.imwrite(filename, image)


    end = time.time()
    print(end - start)

    # Iterate through files and crop as required
    for fn in os.listdir(paths['facesDetected']):
        # Make sure file is not a hidden one etc
        if not fn.startswith('.') and os.path.isfile(os.path.join(paths["facesDetected"], fn)):
            # Open the file checking if it is valid or not. It fails otherwise :-(
            try:
                if not os.path.exists(os.path.join(paths["facesDetected"], fn)):
                    resize_and_crop(os.path.join(paths["facesDetected"], fn), os.path.join(paths["facesDetected"], fn), (300, 300))
                    print(fn + " resized")
                else:
                    print("Resized file exists")
            except:
                pass


    a = count_files(paths["facesDetected"], ".jpg")
    print(str(a) + " faces were identified")
    dims = "10x" + str(a/10)
    print(dims)

    create_montage("files.txt")
