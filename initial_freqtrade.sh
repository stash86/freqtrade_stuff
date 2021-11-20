cd ft_userdata/
mkdir docker
cd docker/
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/docker/Dockerfile.custom
cd ..
curl https://raw.githubusercontent.com/stash86/freqtrade/develop/docker-compose.yml -o docker-compose.yml
sudo docker-compose pull
sudo docker-compose run --rm freqtrade create-userdir --userdir user_data
DIRECTORY=/user_data/
if [ ! -d "$DIRECTORY" ]; then
  mkdir user_data
fi
cd user_data/
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/user_data/atur-telegram.json
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/user_data/atur-binance.json
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/user_data/config-static.json
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/user_data/config.json

