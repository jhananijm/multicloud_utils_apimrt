#!/bin/bash

echo "Triggering script to install packages"
case $1 in
maven)
  echo "Installing Maven packages: apache-maven-3.8.7"
  if [ ! -d /opt/apache-maven-3.8.7 ]
  then
    wget -O /tmp/maven.zip https://dlcdn.apache.org/maven/maven-3/3.8.7/binaries/apache-maven-3.8.7-bin.zip --no-check-certificate
    unzip /tmp/maven.zip -d /opt/
    echo "export PATH=$PATH:/opt/apache-maven-3.8.7/bin" >> ~/.bash_profile
  fi
  source ~/.bash_profile
  mvn --version
  ;;
*)
  exit 1;;
esac
