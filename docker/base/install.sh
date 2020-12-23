#!/bin/bash

apt-get update &&

apt-get install -y gnupg apt-utils debconf-utils dialog gettext-base &&

echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections &&
echo "resolvconf resolvconf/linkify-resolvconf boolean false" | debconf-set-selections &&

apt-key adv --keyserver keyserver.ubuntu.com --recv-key FDC247B7 &&
echo 'deb https://repo.windscribe.com/ubuntu bionic main' | tee /etc/apt/sources.list.d/windscribe-repo.list &&

apt-get update &&

apt-get install -y windscribe-cli expect resolvconf &&

cp /tmp/windscribe_login /windscribe_login.template &&

rm -rf /var/lib/apt/lists/* &&

echo "done"
