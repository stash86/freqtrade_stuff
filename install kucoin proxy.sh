mkdir proxy
cd proxy
git clone https://github.com/mikekonan/exchange-proxy.git
cd exchange-proxy

sudo apt-get purge golang*
sudo add-apt-repository ppa:longsleep/golang-backports
sudo apt update
sudo apt install -y golang-go
sudo apt install -y golang-easyjson

sudo make build

Follow instructions for freqtrade config:
https://github.com/mikekonan/exchange-proxy/blob/main/docs/ops/freqtrade.md 
