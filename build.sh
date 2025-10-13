#!/bin/bash

cd "$(dirname "$0")"

set -e

mkdir -p ./build
mkdir -p ./mp-lib
rm -rf ./build/*
rm -rf ./mp-lib/*

pip install evdev --target ./mp-lib

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

cd build
ls
cpack
