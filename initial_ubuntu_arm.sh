# tested on VM.Standard.A1.Flex with Ubuntu 20.04

# Prepare VPS
sudo su
apt update && apt -y install build-essential pkg-config libblosc-dev  libhdf5-dev libssl-dev

# Install miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-aarch64.sh
bash Miniconda3-py38_4.10.3-Linux-aarch64.sh

# need to exit terminal and re-enter to activate base environment
exit

# install TA-Lib library first ( second half of https://mikestaszel.com/2021/01/23/install-ta-lib-on-m1/ for ARM linux)
sudo su
apt install -y build-essential automake
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
cp /usr/share/automake-1.16/config.guess .
./configure --prefix=/usr
make
make install

cd ..

git clone https://github.com/stash86/freqtrade.git
git clone https://github.com/stash86/freqtrade_stuff.git
cd freqtrade
# git checkout dca-new

# if you want to update conda
conda update -n base -c defaults conda
conda env remove -n freqtrade-conda
conda env create -n freqtrade-conda -f environment.yml
conda activate freqtrade-conda

python3 -m pip install --upgrade pip
python3 -m pip install -e .
