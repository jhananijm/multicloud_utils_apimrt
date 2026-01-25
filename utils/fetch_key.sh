#!/bin/bash


python3 ./scripts/utils/key_gen.py

if [ $? -ne 0 ]
then
    echo "Unable to fetch private or public key from state branch"
fi
