cd ft_userdata/
curl https://raw.githubusercontent.com/freqtrade/freqtrade/develop/docker-compose.yml -o docker-compose.yml
sudo docker-compose pull
sudo docker-compose run --rm freqtrade create-userdir --userdir user_data
sudo docker-compose run --rm freqtrade new-config --config user_data/config.json
