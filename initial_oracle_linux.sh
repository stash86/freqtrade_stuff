sudo yum install -y tmux
tmux
tmux rename-session -t 0 freqtrade
sudo yum-config-manager --disable ol7_UEKR3 ol7_UEKR4
sudo yum-config-manager --enable ol7_UEKR5
sudo yum update -y
sudo systemctl reboot


# after restart
sudo yum-config-manager --enable ol7_addons
sudo systemctl stop docker
sudo yum remove docker
sudo yum install -y yum-utils
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-engine docker-cli
sudo systemctl enable --now docker
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-Linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose



tmux new -t freqtrade

sudo dnf module install -y python38

sudo dnf install -y python38-pip git cmake

wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip

tar -xvf ta-lib-0.4.0-src.tar.gz
cd ta-lib
wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD' -O config.guess
wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD' -O config.sub
./configure --prefix=/usr
make
sudo make install



Detach by pressing Ctrl+b, and then the d key.
tmux attach -t freqtrade
