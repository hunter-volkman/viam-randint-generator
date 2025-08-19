#!/bin/sh
cd `dirname $0`

# Package the module
tar -czf module.tar.gz run.sh setup.sh requirements.txt src meta.json

echo "Build complete: module.tar.gz"