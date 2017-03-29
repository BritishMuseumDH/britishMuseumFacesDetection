#!/usr/bin/env python
from __future__ import print_function
from SPARQLWrapper import SPARQLWrapper, JSON
import urllib
import os
from PIL import Image
import subprocess
import cv2
import argparse
import time

# Retrieve images from British Museum Research Space and perform montage and facial recognition
# Daniel Pett 21/3/2017
# British Museum content is under a CC-BY-SA-NC license
# Tested on Python 2.7.13

__author__ = "Daniel Pett"
__credits__ =  ["Richard Wareham", "Ben O'Steen", "Matthew Vincent"]
__license__ = 'MIT'
__version__ = "1.0.1"
__maintainer__ = "Daniel Pett"
__email__ = "dpett@britishmuseum.org"


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
        modified_path: path to save the modified image.
        size: (width, height) a tuple. Eg (300,300)
        crop_type: 3 options 'top', 'middle' or 'bottom'
    raises:
        Exception: if this script cannot open the file provided by img_path, then the image will not save
        ValueError: thrown if an invalid `crop_type` is provided as an argument
    """
    # Resizing is done in this order: if height is higher than width resize is vertical, default is horizontal resize
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # As mentioned above, the image is scaled and cropped vertically or horizontally depending on the ratio.
    if ratio > img_ratio:
        img = img.resize((size[0], size[0] * img.size[1] / img.size[0]), Image.ANTIALIAS)
        # Switch for position of crop
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
        # Switch for position of crop
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
    """
    Count number of files of a specific extension
    :param path:
    :param extension:
    :return:
    """
    list_dir = []
    list_dir = os.listdir(path)
    count = 0
    for fn in list_dir:
        if fn.endswith(extension):
            # eg: '.jpg'
            count += 1
    return count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A script for retrieving images from British Museum Research Space and '
                                             'perform montage and facial recognition')

    parser.add_argument('-p', '--path', help='The path in which to run this script', required=True)
    # An example would be: --path '/Users/danielpett/githubProjects/scripts/'

    parser.add_argument('-m', '--montages', help='The path in which to place montage images', required=True)
    # An example would be: --montages '/Users/danielpett/githubProjects/scripts/montages/'

    parser.add_argument('-d', '--download', help='The path in which to place downloaded images', required=True)
    # An example would be: --download '/Users/danielpett/githubProjects/scripts/bmimages/'

    parser.add_argument('-f', '--faces', help='The path in which to place face detected images', required=True)
    # An example would be: --faces '/Users/danielpett/githubProjects/scripts/facesDetected/'

    parser.add_argument('-r', '--resized', help='The path in which to place resized images', required=True)
    # An example would be: --resized '/Users/danielpett/githubProjects/scripts/bmimagesResized/'

    parser.add_argument('-s', '--size', help='The resize dimensions', required=False, default=300)
    # An example would be: --resized '/Users/danielpett/githubProjects/scripts/bmimagesResized/'

    parser.add_argument('-o', '--output', help='The file name output for image magick', required="false", default='britishMuseumImages')
    # An example would be 'britishMuseumPortraits'

    parser.add_argument('-t', '--template', help='The spaqrl query template to use', required="false", default='default')
    # An example would be 'default' as this is concatenated to default.txt

    parser.add_argument('-q', '--query', help='The spaqrl query template to use', required="false", default='bust')
    # An example would be 'bust'

    # Parse arguments
    args = parser.parse_args()

    # Set base path
    basePath = args.path

    # Define the base directories
    paths = {x: os.path.join(basePath, x) for x in [args.download, args.resized, args.montages, args.faces, 'opencv']}

    # Create them if they don't already exist
    for path in paths.values():
        if not os.path.exists(path):
            os.makedirs(path)

    # Set up your sparql endpoint
    sparql = SPARQLWrapper("http://collection.britishmuseum.org/sparql")

    # Read text file sparql query
    with open("sparql/" + args.template + ".txt", "r") as sparqlQuery:
        # Format the query string retrieved from the text file with simple replacement
        query = sparqlQuery.read().format(string = args.query)

    # Return the query for the user to see
    print("Your sparql query reads as: \n" + query)

    # Set your query
    sparql.setQuery(query)

    # Return the JSON triples
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    # Open the file for writing urls (this is for image magick)
    listImages = open(os.path.join(paths[args.resized], "files.txt"), 'w')

    # Iterate over the results
    for result in results["results"]["bindings"]:
        image = result["image"]["value"]
        if os.path.isfile(os.path.join(paths[args.download], os.path.basename(image))):
            print("File already exists")
        else:
            path = os.path.join(paths[args.download], os.path.basename(image))
            urllib.urlretrieve(image, path)
            print("Image " + os.path.basename(image) + " downloaded")

    for fn in os.listdir(paths[args.download]):
        if not fn.startswith('.'):
            listImages.write(os.path.join(paths[args.resized], os.path.basename(fn)) + "\n")
            print("Image path written to file")

    # Iterate through files and crop as required
    for fn in os.listdir(paths[args.download]):
        # Make sure file is not a hidden one etc
        if not fn.startswith('.') and os.path.isfile(os.path.join(paths[args.download], fn)):
            # Open the file checking if it is valid or not. It fails otherwise :-(
            try:
                if not os.path.exists(os.path.join(paths[args.resized], fn)):
                    resize_and_crop(os.path.join(paths[args.download], fn), os.path.join(paths[args.resized], fn), (args.size, args.size))
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
    for fn in os.listdir(paths[args.download]):
        if not fn.startswith('.'):
            print("Detecting faces in " + os.path.join(paths[args.download], fn))
            image = cv2.imread(os.path.join(paths[args.download], fn))

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
            print("Found {0} faces within the image".format(len(faces)))
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    image = image[y-top:y+h+bottom, x-left:x+w+right]
                    filename = os.path.join(paths[args.faces], "cropped_{1}_{0}".format(str(fn),str(x)))
                    if not os.path.exists(filename):
                        cv2.imwrite(filename, image)
                        filesize = os.stat(filename).st_size
                        try:
                            if not filesize ==0:
                                resize_and_crop(filename, filename, (args.size, args.size),crop_type='middle')
                            else:
                                print(filename + " is likely to be broken.")
                                os.remove(filename)
                                print(filename + " has therefore been removed.")
                        except:
                            pass

    end = time.time()
    print("The time taken to process face detection was: " + "--- %s seconds ---" % (end - start))

    # Iterate through files and crop as required
    for fn in os.listdir(paths[args.faces]):
        # Make sure file is not a hidden one etc
        if not fn.startswith('.') and os.path.isfile(os.path.join(paths[args.faces], fn)):
            # Open the file checking if it is valid or not. It fails otherwise :-(
            try:
                if not os.path.exists(os.path.join(paths[args.faces], fn)):
                    resize_and_crop(os.path.join(paths[args.faces], fn), os.path.join(paths[args.faces], fn), (args.size, args.size))
                    print(fn + " resized")
                else:
                    print("Resized file exists")
            except:
                pass

    a = count_files(paths[args.faces], ".jpg")
    print(str(a) + " faces were identified in total")
    dims = "10x" + str(a/10)
    print("The dimensions of the montage are " + dims)


    def create_montage(fn):
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
                print("Now creating image montage of all retrieved images")
                subprocess.call("montage @" + os.path.basename(
                    fn) + " -border 0 -geometry 660x -tile 10x10 " + "/".join([args.montages, args.output]) + ".jpg",
                                shell=True)
                print("Now resizing image montage of all retrieved images")
                subprocess.call(
                    "convert " + "/".join([args.montages, args.output]) + ".jpg -resize 750 "
                    + "/".join([args.montages, args.output]) + "_montage_750w.jpg",
                    shell=True)
                # This call makes a montage of the faces detected
                print("Now creating image montage of all faces detected in images")
                subprocess.call(
                    "montage -border 0 -geometry 660x -tile " + dims + " " + args.faces + "/* "
                    + "/".join([args.montages, args.output]) + "Faces.jpg",
                    shell=True)
                print("Now resizing image montage of all faces detected in images")
                subprocess.call(
                    "convert " + "/".join([args.montages, args.output]) + "Faces.jpg -resize 750 " +
                    "/".join([args.montages, args.output]) + "Faces_montage_750w.jpg",
                    shell=True)
            except:
                # The process failed
                raise ValueError("Montage generation failed")

    create_montage("files.txt")
    print("Facial detection complete")
