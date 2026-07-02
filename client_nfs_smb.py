#!/usr/bin/env python3

import os
import platform
import time
from datetime import datetime
import json
import random
import string
from smb_client import SMBClient
import subprocess
import csv
import logging

# Create logs folder
if not os.path.exists('logs'):
    os.makedirs('logs')
# create collected_data folder
if not os.path.exists('collected_data'):
    os.makedirs('collected_data')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='logs/client_nfs_smb.log')


# CSV file setup
csv_file = 'collected_data/client_througput.csv'

# Ensure CSV file has the correct header
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["mode", "filepath", "event_type", "timestamp", "rsize", "wsize", "nfsvers", "tcp", "size_MB", "throughput_Mbps", "latency_ms"])

def write_to_csv(mode, file_path, size, operation, throughput, rsize, wsize, nfsvers, tcp, latency):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([mode, file_path, operation, timestamp, rsize, wsize, nfsvers, tcp, size, throughput, latency])


def generate_random_data(size):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode('utf-8')

def create_test_file(filename, size):
    if platform.system() == 'Windows':
        file_path = os.path.join(os.getenv('TEMP'), filename)
    else:
        file_path = os.path.join('/tmp', filename)
    with open(file_path, 'wb') as f:
        f.write(generate_random_data(size))

    return file_path

def smb_upload_read_test(smb_client, file_name, file_size):
    # Create a local file to upload
    local_file_path = create_test_file(file_name, file_size)

    # Upload the file to the SMB share
    start_time = time.time()

    smb_client.upload_file(local_file_path, file_name)

    upload_time = time.time() - start_time
    file_size = os.path.getsize(local_file_path)
    write_throughput = file_size / upload_time / (1024 * 1024)  # MBps
    # print(f"Upload throughput: {throughput:.2f} MBps")

    # remove local file
    os.remove(local_file_path)

    # Read the file from the SMB share
    start_time = time.time()

    smb_client.download_file(file_name, local_file_path)

    read_time = time.time() - start_time
    file_size = os.path.getsize(local_file_path)
    read_throughput = file_size / read_time / (1024 * 1024)  # MBps

    # remove local file
    os.remove(local_file_path)

    return upload_time, read_time, write_throughput, read_throughput

def nfs_upload_read_test(local_mount_point, file_name, file_size):
    # Create a random data file

    data = generate_random_data(file_size)

    # file_path = create_test_file(file_name, file_size)

    # Upload the file to the NFS share
    start_time = time.time()
    with open(os.path.join(local_mount_point, file_name), 'wb') as f:
        f.write(data)

    upload_time = time.time() - start_time
    write_throughput = file_size / upload_time / (1024 * 1024)  # MBps

    # Read the file from the NFS share
    start_time = time.time()
    with open(os.path.join(local_mount_point, file_name), 'rb') as f:
        f.read()
    read_time = time.time() - start_time

    read_throughput = file_size / read_time / (1024 * 1024)  # MBps

    return upload_time, read_time, write_throughput, read_throughput

def mount_nfs(nfs_config, local_mount_point):
    server = nfs_config['server']
    remote_path = nfs_config['remote_path']
    nfsvers = nfs_config.get('nfsvers', 4)  # default to NFSv4
    tcp = nfs_config.get('tcp', False)  # default to UDP
    rsize = nfs_config.get('rsize', 1048576)  # default to 1MB
    wsize = nfs_config.get('wsize', 1048576)  # default to 1MB


    if platform.system() == 'Windows':
        # interact with subprocess output
        # mount -o anon,nfsvers=3,rsize=32768,wsize=32768,tcp nfs_server:/nfs_export_path Z:
        options = f"anon,nfsvers={nfsvers},rsize={rsize},wsize={wsize}"
        if tcp:
            options += ",tcp"
        result = subprocess.run(["mount", "-o", options, f"{server}:{remote_path}", local_mount_point], capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr)
            pass
    else:
        # subprocess.run(["mount", "-t", "nfs", f"{server}:{remote_path}", local_mount_point], check=True)
        #  sudo mount -t nfs -o rw,noatime,nodiratime,tcp,rsize=32768,wsize=32768,hard,intr 192.168.1.100:/srv/nfs/export /mnt/nfs_export
        options = f"nfsvers={nfsvers},rsize={rsize},wsize={wsize}"
        if tcp:
            options += ",tcp"
        result = subprocess.run(["sudo", "mount", "-t", "nfs", "-o", options, f"{server}:{remote_path}", local_mount_point], capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr)
            pass

def unmount_nfs(local_mount_point):
    if platform.system() == 'Windows':
        subprocess.run(["umount", local_mount_point], check=True)
    elif platform.system() == 'Linux':
        subprocess.run(["sudo", "umount", local_mount_point], check=True)


def main():
    with open('client_config.json', 'r') as f:
        config = json.load(f)

    smb_config = config.get('smb')
    nfs_config = config.get('nfs')
    operations_config = config.get('operations')



    num_operations = operations_config.get('num_operations', 2)
    file_path = operations_config.get('file_path', 'testfile')

    if smb_config and smb_config.get('enabled', False):

        smb_client = SMBClient(smb_config['server'], smb_config['share_name'], smb_config['username'], smb_config['password'], smb_config['domain_name'])

        print(f"Running SMB tests...")
        for i in range(num_operations):
            file_size = random.randint(10 * 1024 * 1024, 50 * 1024 * 1024)
            upload_time, read_time,  write_throughput, read_throughput = smb_upload_read_test(
                smb_client, file_path, file_size
            )
            print(f"SMB Operation {i+1}/{num_operations}: Upload time = {upload_time:.4f}s, Read time = {read_time:.4f}s, Write Throughput = {write_throughput:.2f} MBps, Read Throughput = {read_throughput:.2f} MBps")
            logging.info(f"SMB Operation {i+1}/{num_operations}: Upload time = {upload_time:.4f}s, Read time = {read_time:.4f}s, Write Throughput = {write_throughput:.2f} MBps, Read Throughput = {read_throughput:.2f} MBps")

            file_size_mb = file_size / (1024 * 1024)
            file_size_mb = round(file_size_mb, 2)
            # cut float to 2 decimal places
            write_throughput = round(write_throughput, 2)
            read_throughput = round(read_throughput, 2)
            upload_latency= round(upload_time, 4) * 1000  # ms
            read_latency = round(read_time, 4) * 1000  # ms
            
            write_to_csv("smb", file_path, file_size_mb, "upload", write_throughput, 0, 0, 0, 0, upload_latency)
            write_to_csv("smb", file_path, file_size_mb, "read", read_throughput, 0, 0, 0, 0, read_latency)
            

    if nfs_config and nfs_config.get('enabled', False):

        if platform.system() == 'Windows':
            local_mount_point = nfs_config['windows_local_mount_point']
        else:
            local_mount_point = nfs_config['linux_local_mount_point']
        # Mount the NFS share
        try:
            mount_nfs(nfs_config, local_mount_point)
        except Exception as e:
            print(f"Failed to mount NFS share: {e}")
            logging.error(f"Failed to mount NFS share: {e}")
            return

        print(f"Running NFS tests...")
        for i in range(num_operations):
            file_size = random.randint(10 * 1024 * 1024, 100 * 1024 * 1024)
            upload_time, read_time,  write_throughput, read_throughput = nfs_upload_read_test(
                local_mount_point, file_path, file_size
            )
            print(f"NFS Operation {i+1}/{num_operations}: Upload time = {upload_time:.4f}s, Read time = {read_time:.4f}s, Write Throughput = {write_throughput:.2f} MBps, Read Throughput = {read_throughput:.2f} MBps")
            logging.info(f"NFS Operation {i+1}/{num_operations}: Upload time = {upload_time:.4f}s, Read time = {read_time:.4f}s, Write Throughput = {write_throughput:.2f} MBps, Read Throughput = {read_throughput:.2f} MBps")

            wsize = nfs_config['client_settings'].get('wsize')
            rsize = nfs_config['client_settings'].get('rsize')
            nfsvers = nfs_config['client_settings'].get('nfsvers')
            tcp = nfs_config['client_settings'].get('tcp')

            file_size_mb = file_size / (1024 * 1024)
            file_size_mb = round(file_size_mb, 2)
            # cut float to 2 decimal places
            write_throughput = round(write_throughput, 2)
            read_throughput = round(read_throughput, 2)
            upload_time = round(upload_time, 4) * 1000
            read_time = round(read_time, 4) * 1000

            write_to_csv("nfs", file_path, file_size_mb, "upload", write_throughput, rsize, wsize, nfsvers, tcp, upload_time)
            write_to_csv("nfs", file_path, file_size_mb, "read", read_throughput, rsize, wsize, nfsvers, tcp, read_time)

        # Unmount the NFS share
        unmount_nfs(local_mount_point)

if __name__ == '__main__':
    main()
