#!/bin/sh

# Install pyinstaller with pip3 install pyinstaller

rm -rf dist/powerd build/*
pyinstaller --osx-bundle-identifier com.apple.metadata.mds_stores.power --bootloader-ignore-signals --strip --onefile powerd.py 
