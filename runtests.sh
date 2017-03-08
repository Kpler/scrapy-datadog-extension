#!/bin/bash

###
# Setup virtualenv
###

virtualenv --python=python2.7 /home/jenkins/.virtualenvs/jenkins

wrapper=
for file in "/usr/share/virtualenvwrapper/virtualenvwrapper.sh" "/usr/local/bin/virtualenvwrapper.sh"
do
    echo -n "Does \`${file}' exists ? "
    [ -f "${file}" ] && { wrapper="$file" ; echo "yes" ; } || { echo "no" ; }
    [ -n "${wrapper}" ] && break
done
[ -z "${wrapper}" ] && { echo "Please install virtualenvwrapper" 1>&2 ; exit 1 ; }
venv_name="jenkins"
export WORKON_HOME="/home/jenkins/.virtualenvs"
source "${wrapper}"

[ -d "$HOME/.virtualenvs/${venv_name}" ] || { mkvirtualenv -a . "${venv_name}" ; }
workon "${venv_name}" 2> /dev/null
if [ "0" != "$?" ]
then
    echo "Please setup a virtualenv named \`${venv_name}' for this test-runner."
    exit 1
fi

set -x

###
# Intalling/updating dependencies and package
###

wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py

pip install --upgrade -r dev-requirements.txt
pip install -e .

###
# Environment is set. Start the real work
###

nosetests -v --stop
