#!/bin/bash

cd "$(dirname "$0")"

set -e

mkdir -p ./build
rm -rf ./build/*

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

cd build
ls
cpack
