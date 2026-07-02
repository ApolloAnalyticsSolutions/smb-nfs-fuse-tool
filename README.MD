# 1. Setup NFS/SMB server 
sudo chmod +x setup.sh
sudo ./setup.sh

# 2. Run Fuse Monitor
sudo python3 server_fuse_monitor.py

# 3. Run client 
sudo python3 client_nfs_smb.py

...

# smb-nfs-fuse-tool
# smb-nfs-fuse-tool
