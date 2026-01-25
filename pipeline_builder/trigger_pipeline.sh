#!/bin/bash

echo -e "\nInstalling pre-requisite packages...\n"
pip3 install -r requirements.txt > run.log 2>&1

if [ $? -ne 0 ]
then
    echo "Installing of pre-requisite packages failed"
    echo -e "Check run.log for details\n"
    exit 1
fi

python3 pipeline_builder.py $1 $2 $3 $4