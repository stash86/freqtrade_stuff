mkdir proxy
cd proxy
git clone https://github.com/mikekonan/exchange-proxy.git
cd exchange-proxy

sudo apt-get -y purge golang*
sudo add-apt-repository -y ppa:longsleep/golang-backports
sudo apt update
sudo apt install -y golang-go golang-easyjson
sudo make build