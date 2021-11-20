screen -S freqtrade
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
mkdir ft_userdata
sudo wget https://raw.githubusercontent.com/stash86/freqtrade/develop/initial_freqtrade.sh
bash initial_freqtrade.sh