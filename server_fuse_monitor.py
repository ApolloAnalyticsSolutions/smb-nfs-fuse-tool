#!/usr/bin/env python3

import os
import json
import sys
import errno
import logging
import pyinotify
import csv
from fuse import FUSE, Operations, FuseOSError
from datetime import datetime

# create logs
if not os.path.exists('logs'):
    os.makedirs('logs')
    
# Configure logging
logging.basicConfig(filename='logs/fuse_utils.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# CSV file setup
csv_file = 'collected_data/IO_events.csv'

# Ensure CSV file has the correct header
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["filepath", "size", "event_type", "timestamp"])

def write_to_csv(filepath, size, event_type):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([filepath, size, event_type, timestamp])

class FuseMonitor(Operations):
    def __init__(self, root):
        self.root = root

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        try:
            st = os.lstat(full_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime', 'st_gid',
                                                            'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        except OSError:
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def read(self, path, size, offset, fh):
        full_path = self._full_path(path)
        with open(full_path, 'rb') as f:
            f.seek(offset)
            data = f.read(size)
        logging.info(f"Read: {path} (size: {size}, offset: {offset})")
        print(f"Read: {path} (size: {size}, offset: {offset})")
        write_to_csv(path, size, 'READ')
        return data

    def write(self, path, data, offset, fh):
        full_path = self._full_path(path)
        with open(full_path, 'r+b') as f:
            f.seek(offset)
            f.write(data)
        logging.info(f"Write: {path} (size: {len(data)}, offset: {offset})")
        print(f"Write: {path} (size: {len(data)}, offset: {offset})")
        write_to_csv(path, len(data), 'WRITE')
        return len(data)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+b') as f:
            f.truncate(length)
        logging.info(f"Truncate: {path} to length {length}")
        return 0

    def open(self, path, flags):
        full_path = self._full_path(path)
        logging.info(f"Open: {path}")
        return os.open(full_path, flags)

    def release(self, path, fh):
        logging.info(f"Release: {path}")
        return os.close(fh)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        logging.info(f"Create: {path} (mode: {mode})")
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def unlink(self, path):
        full_path = self._full_path(path)
        logging.info(f"Unlink: {path}")
        return os.unlink(full_path)

def main(mountpoint, root):
    logging.info(f"Mounting FUSE filesystem at {mountpoint}, root: {root}")
    print(f"Mounting FUSE filesystem at {mountpoint}, root: {root}")
    FUSE(FuseMonitor(root), mountpoint, nothreads=True, foreground=True, allow_other=True, nonempty=True)

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        logging.info(f"Write: {event.pathname}")
        size = os.path.getsize(event.pathname) if os.path.exists(event.pathname) else 0
        write_to_csv(event.pathname, size, 'WRITE')

    # def process_IN_ACCESS(self, event):
    #     logging.info(f"File accessed: {event.pathname}")
    #     size = os.path.getsize(event.pathname) if os.path.exists(event.pathname) else 0
    #     write_to_csv(event.pathname, size, 'access')

    def process_IN_CLOSE_NOWRITE(self, event):
        if event.dir:
            return
        logging.info(f"Reading: {event.pathname}")
        size = os.path.getsize(event.pathname) if os.path.exists(event.pathname) else 0
        write_to_csv(event.pathname, size, 'READ')

def start_inotify_watch(paths):
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_ACCESS | pyinotify.IN_CLOSE_NOWRITE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    for path in paths:
        wm.add_watch(path, mask, rec=True)
    notifier.loop()

if __name__ == '__main__':
    from multiprocessing import Process

    # load server_config.json
    with open('server_config.json', 'r') as f:
        config = json.load(f)

    smb_mountpoint = config['fuse']['fuse_smb_mount_point']
    smb_root = config['fuse']['fuse_smb_root']
    nfs_mountpoint = config['fuse']['fuse_nfs_mount_point']
    nfs_root = config['fuse']['fuse_nfs_root']


    smb_share = config['smb']['share_name'] 
    smb_share = smb_share if smb_share.startswith('/') else '/' + smb_share
    nfs_export = config['nfs']['export_path']

    # Paths to watch
    paths_to_watch = [smb_share, nfs_export]

    # Start inotify watch on the specified paths
    p_inotify = Process(target=start_inotify_watch, args=(paths_to_watch,))
    p_inotify.start()

    # Start FUSE filesystem for SMB share
    p_fuse_smb = Process(target=main, args=(smb_mountpoint, smb_root))
    p_fuse_smb.start()

    # Start FUSE filesystem for NFS export
    p_fuse_nfs = Process(target=main, args=(nfs_mountpoint, nfs_root))
    p_fuse_nfs.start()

    p_fuse_smb.join()
    p_fuse_nfs.join()
    p_inotify.terminate()
