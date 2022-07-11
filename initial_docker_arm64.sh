sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
sudo apt-get -y install apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-compose python3-pip

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

# # Docker without sudo
# sudo groupadd docker
# sudo usermod -aG docker $USER
# newgrp docker

# sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/swap_ubuntu_amd.sh
# bash swap_ubuntu_amd.sh
# mkdir ft_userdata
# sudo chown -R ubuntu:ubuntu ./freqtrade
sudo chmod -R 0777 ./freqtrade
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/initial_freqtrade.sh
bash initial_freqtrade.sh