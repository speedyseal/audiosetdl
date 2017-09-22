#!/usr/bin/env bash

BIN_DIR="./bin"
CONDA_DIR="$BIN_DIR/miniconda"
CONDA_BIN_DIR="$CONDA_DIR/bin"

# Make bin folder
mkdir -p $BIN_DIR

# Install Anaconda
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh -O $BIN_DIR/Miniconda2-latest-Linux-x86_64.sh
bash $BIN_DIR/Miniconda2-latest-Linux-x86_64.sh -p $CONDA_DIR -b

# Install conda dependencies
$CONDA_BIN_DIR/conda install -c conda-forge ffmpeg -y
$CONDA_BIN_DIR/pip install --upgrade -r ./requirements.txt
