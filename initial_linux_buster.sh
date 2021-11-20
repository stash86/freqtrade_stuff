sudo apt-get -y install python3-pip python3-venv libatlas-base-dev cmake git wget
sudo echo "[global]\nextra-index-url=https://www.piwheels.org/simple" > tee /etc/pip.conf
git clone https://github.com/stash86/freqtrade.git
cd freqtrade
bash setup.sh -i