#/bin/bash
sudo -H -E pip install git+ssh://git@github.com/ecederstrand/exchangelib.git
git update-index --assume-unchanged credentials
