# syntax=docker/dockerfile:1

FROM jupyter/minimal-notebook

WORKDIR ./fx-options-ukraine-war

# change active user to root
USER root 

# create the directory
RUN mkdir lib

# set jovyan as owner of the directory
RUN chown jovyan lib

# change back to user jovyan
USER jovyan

# install packages
# fro mrequirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# external, with git
RUN git clone https://github.com/ipozdeev/optools.git ./lib/optools

# set PYTHONPATH for python to find the external sources
ENV PYTHONPATH=${PYTHONPATH}:/home/jovyan/fx-options-ukraine-war/lib

# set PROJECT_ROOT (since .env is not being copied)
ENV PROJECT_ROOT=/home/jovyan/fx-options-ukraine-war

# copy files
COPY . .
