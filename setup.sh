#!/bin/bash

# Determine the operating system
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Unsupported OS."
    exit 1
fi

# Function to install dependencies on Ubuntu
install_ubuntu_dependencies() {
    echo "Installing dependencies for Ubuntu..."
    sudo apt-get update
    sudo apt-get install -y --no-install-recommends \
        smbclient \
        nfs-common \
        nfs-kernel-server \
        fuse \
        samba \
        jq \
        cifs-utils \
        python3 \
        python3-pip
}

# Function to install dependencies on CentOS
install_centos_dependencies() {
    echo "Installing dependencies for CentOS..."
    sudo yum install -y \
        samba \
        samba-client \
        samba-common\
        nfs-utils \
        fuse \
        cifs-utils\
        jq \
        python3 \
        python3-pip
}

# Install dependencies based on OS
if [ "$OS" == "ubuntu" ]; then
    install_ubuntu_dependencies
elif [ "$OS" == "centos" ] || [ "$OS" == "rhel" ]; then
    install_centos_dependencies
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Common setup for both Ubuntu and CentOS
echo "Setting up the SMB/NFS server..."

# Read server_config.json and get nfs_export_path smb->share_name
nfs_export_path=$(jq -r '.nfs.export_path' server_config.json)
echo "Creating NFS export at $nfs_export_path"
sudo mkdir -p "$nfs_export_path"
sudo chmod -R 0777 "$nfs_export_path"

# Read server_config.json and get smb_share_path
smb_share_path=$(jq -r '.smb.share_name' server_config.json)
echo "Creating SMB share at $smb_share_path"
sudo mkdir -p "$smb_share_path"
sudo chmod -R 0777 "$smb_share_path"

# Set up a simple SMB share
if grep -q "\[smb_share\]" /etc/samba/smb.conf; then
    echo "SMB share already exists in /etc/samba/smb.conf"
else
    echo "SMB share does not exist in /etc/samba/smb.conf"
    echo "[smb_share]
            path = $smb_share_path
            browseable = yes
            read only = no
            guest ok = yes
            writable = yes
            create mask = 0777
            directory mask = 0777" | sudo tee -a /etc/samba/smb.conf > /dev/null
fi

# start samba server for ubuntu and centos and make it persistent when booting
sudo systemctl start smb nmb
sudo systemctl enable smb nmb

# Adjust the firewall settings to allow Samba traffic:
if [ "$OS" == "ubuntu" ]; then
    sudo ufw allow Samba
else
    sudo firewall-cmd --permanent --zone=public --add-service=samba
    sudo firewall-cmd --reload
fi


# Start NFS kernel server
if [ "$OS" == "ubuntu" ]; then
    sudo service nfs-kernel-server start
else
    sudo systemctl start nfs-server
fi



# Set up a simple NFS export
if grep -q "$nfs_export_path" /etc/exports; then
    echo "NFS export already exists in /etc/exports"
else
    echo "NFS export does not exist in /etc/exports"
    echo "$nfs_export_path *(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports > /dev/null
fi

sudo exportfs -a

# Edit /etc/default/nfs-kernel-server or /etc/nfs.conf
rpcnfsdcount=$(jq -r '.nfs.server_settings.rpcnfsdcount' server_config.json)
lease_time=$(jq -r '.nfs.server_settings.lease_time' server_config.json)
grace_time=$(jq -r '.nfs.server_settings.grace_time' server_config.json)

if [ "$OS" == "ubuntu" ]; then
    echo "Setting RPCNFSDCOUNT and NFSD_OPTS in /etc/default/nfs-kernel-server"
    sudo sed -i "s/RPCNFSDCOUNT=.*/RPCNFSDCOUNT=$rpcnfsdcount/" /etc/default/nfs-kernel-server
    if grep -q "NFSD_OPTS" /etc/default/nfs-kernel-server; then
        sudo sed -i "s/NFSD_OPTS=.*/NFSD_OPTS=\"--lease-time=$lease_time --grace-time=$grace_time\"/" /etc/default/nfs-kernel-server
    else
        echo "NFSD_OPTS=\"--lease-time=$lease_time --grace-time=$grace_time\"" | sudo tee -a /etc/default/nfs-kernel-server > /dev/null
    fi
else
    echo "Setting NFSD options in /etc/nfs.conf"
    sudo bash -c "echo '[nfsd]' >> /etc/nfs.conf"
    sudo bash -c "echo 'nfsd count = $rpcnfsdcount' >> /etc/nfs.conf"
    sudo bash -c "echo 'lease-time = $lease_time' >> /etc/nfs.conf"
    sudo bash -c "echo 'grace-time = $grace_time' >> /etc/nfs.conf"
fi

# Restart NFS server
if [ "$OS" == "ubuntu" ]; then
    sudo service nfs-kernel-server restart
else
    sudo systemctl restart nfs-server
fi

# Set up a FUSE mountEnable FUSE user_allow_other

if [ "$OS" == "ubuntu" ]; then
    sudo sed -i 's/#user_allow_other/user_allow_other/' /etc/fuse.conf
else
    sudo sed -i 's/# user_allow_other/user_allow_other/' /etc/fuse.conf
fi


# Create a directory for the FUSE mount for smb, nfs, root
fuse_smb_mount_point=$(jq -r '.fuse.fuse_smb_mount_point' server_config.json)
fuse_nfs_mount_point=$(jq -r '.fuse.fuse_nfs_mount_point' server_config.json)
fuse_smb_root=$(jq -r '.fuse.fuse_smb_root' server_config.json)
fuse_nfs_root=$(jq -r '.fuse.fuse_nfs_root' server_config.json)

sudo mkdir -p "$fuse_smb_mount_point"
sudo mkdir -p "$fuse_nfs_mount_point"
sudo mkdir -p "$fuse_smb_root"
sudo mkdir -p "$fuse_nfs_root"

sudo chmod -R 0777 "$fuse_smb_mount_point"
sudo chmod -R 0777 "$fuse_nfs_mount_point"
sudo chmod -R 0777 "$fuse_smb_root"
sudo chmod -R 0777 "$fuse_nfs_root"

# Mount the SMB share using FUSE
smb_server=$(jq -r '.smb.server' server_config.json)
username=$(jq -r '.smb.username' server_config.json)
password=$(jq -r '.smb.password' server_config.json)
sudo mount -t cifs //"$smb_server""$smb_share_path" "$fuse_smb_root" -o username="$username",password="$password",uid=$(id -u),gid=$(id -g),file_mode=0777,dir_mode=0777
echo "mount -t //$smb_server$smb_share_path $fuse_smb_root cifs username=$username,password=$password,uid=$(id -u),gid=$(id -g),file_mode=0777,dir_mode=0777 0 0"

# Make the mount persistent across reboots
if grep -q "$fuse_smb_root" /etc/fstab; then
    echo "SMB share already exists in /etc/fstab"
else
    echo "//$smb_server$smb_share_path $fuse_smb_root cifs username=$username,password=$password,uid=$(id -u),gid=$(id -g),file_mode=0777,dir_mode=0777 0 0" | sudo tee -a /etc/fstab > /dev/null
fi

# Mount the NFS export using FUSE
nfs_server=$(jq -r '.nfs.server' server_config.json)
sudo mount -t nfs "$nfs_server":"$nfs_export_path" "$fuse_nfs_root"

# Make the mount persistent across reboots
if grep -q "$nfs_server:$nfs_export_path $fuse_nfs_root" /etc/fstab; then
    echo "NFS export already exists in /etc/fstab"
else
    echo "$nfs_server":"$nfs_export_path" "$fuse_nfs_root" nfs defaults 0 0 | sudo tee -a /etc/fstab > /dev/null
fi

# Set the current directory to where the script is located
cd "$(dirname "$0")"

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt

# Run the main script
# python3 src/main.py

