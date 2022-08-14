sudo apt-get -y install screen python3-pip python3-venv libatlas-base-dev cmake git wget
sudo echo "[global]\nextra-index-url=https://www.piwheels.org/simple" > tee /etc/pip.conf
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
sudo apt-get -y install ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-compose
git clone https://github.com/stash86/freqtrade
chmod -R 0777 ./freqtrade
cd freqtrade
