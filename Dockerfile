FROM debian:jessie

RUN apt-get update
RUN apt-get install -y python python-dev python-pip python-virtualenv python-opencv python-matplotlib imagemagick
RUN pip install SPARQLWrapper Pillow

# Define working directory.
WORKDIR /bmfaces
