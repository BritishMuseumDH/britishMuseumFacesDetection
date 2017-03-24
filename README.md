## A demonstration script for facial detection

This repository holds a sample terminal script for interacting with the British Museum's RDF endpoint to retrieve images and then
using OpenCV, recognise faces within the images. These are then cropped and stored in a directory on your machine.

This is a very simple example and pulls busts (100 of them) from the British Museum collection and uses them to
create image montages. Within the folder are all the files pulled from the example script.

An example detected face can be shown below:

Original image

![](bmimagesResized/AN00587263_001_l.jpg)

Detected face

![](facesDetected/cropped_272_AN00587263_001_l.jpg)

There are also two montages created at the end of this script:

All images originally pulled from RDF:

![](montages/bmPortraitBusts_montage_750w.jpg)

All faces identified within the original images:

![](montages/bmPortraitBustsFaces_montage_750w.jpg)

**I am rubbish at Python, so this is a learning project.**

# To use

Clone this folder to your computer:

`$ git clone https://github.com/BritishMuseumDH/britishMuseumFaceDetection.git`

Change to the directory:

`$ cd britishMuseumFaceDetection`

Install the requirements (I recommend doing this in a virtual environment):

`$ pip install -r requirements.txt`

Now run the script (for example):

`$ python britishMuseumFaces.py -p . -d bmimages -f facesDetected -r bmimagesResized -m montages -s 200 -o 'bmImages' `

There are several arguments that you use for this script:

Mandatory:
* Path -p or --path
* Download directory -d or --directory
* Faces directory -f or --faces
* Resize directory -r or --resized
* Montages directory -m or --montages

Optional
* Size of cropped image -s or --size (default 300)
* Output file -o or --output (default bmImages)

This should run and output any error messages to your terminal.

# License

MIT for script. CC-BY-NC-SA for all image content, copyright the Trustees of the British Museum.

# Author

Daniel Pett, Digital Humanities Lead, British Museum
