import socket
import logging
from smb.SMBConnection import SMBConnection
import os

# Configure logging
# Create logs folder
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(filename="logs/smb_client.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SMBClient:
    def __init__(self, server_name, share_name, username, password, domain_name, client_name='smb_client'):
        """
        Initialize the SMBClient with the necessary connection details.
        """
        self.server_name = server_name
        self.share_name = share_name
        self.username = username
        self.password = password
        self.domain_name = domain_name
        self.client_name = client_name
        self.conn = self.connect()


    def connect(self):
        """
        Connect to the SMB server.
        """
        logging.info(f"Attempting to connect to SMB server {self.server_name}" )

        conn = SMBConnection(
            username=self.username,
            password=self.password,
            my_name=self.client_name,
            remote_name=self.server_name,
            domain=self.domain_name,
            use_ntlm_v2=True
        )

        try:
            if not conn.connect(self.server_name, 445):
                raise ConnectionError(f"Failed to connect to {self.server_name}")
        except Exception as e:
            logging.error(f"Error connecting to SMB server: {e}")
            raise

        return conn

    def list_files(self, remote_dir):
        """
        List files in the specified remote directory.
        """
        logging.info(f"Listing files in {remote_dir} on {self.share_name}")
        return self.conn.listPath(self.share_name, remote_dir)

    def upload_file(self, local_filepath, remote_filepath):
        """
        Upload a file to the specified remote filepath.
        """
        print("smb_share", self.share_name)
        logging.info(f"Uploading {local_filepath} to {remote_filepath} on {self.share_name}")
        with open(local_filepath, 'rb') as file:
            self.conn.storeFile(self.share_name, remote_filepath, file)

    def download_file(self, remote_filepath, local_filepath):
        """
        Download a file from the specified remote filepath.
        """
        logging.info(f"Downloading {remote_filepath} from {self.share_name} to {local_filepath}")
        with open(local_filepath, 'wb') as file:
            self.conn.retrieveFile(self.share_name, remote_filepath, file)

    def delete_file(self, remote_filepath):
        """
        Delete the specified file from the remote share.
        """
        logging.info(f"Deleting {remote_filepath} from {self.share_name}")
        self.conn.deleteFiles(self.share_name, remote_filepath)

    def create_directory(self, remote_dir):
        """
        Create a directory in the remote share.
        """
        logging.info(f"Creating directory {remote_dir} on {self.share_name}")
        self.conn.createDirectory(self.share_name, remote_dir)

    def list_shares(self):
        """
        List all available SMB shares.
        """
        logging.info("Listing available SMB shares")
        return self.conn.listShares()

    def open_file(self, remote_filepath, mode):
        """
        Open a file in the specified mode.
        """
        try:
            logging.info(f"Opening {remote_filepath} on {self.share_name} with mode '{mode}'")
            return self.conn.openFile(self.share_name, remote_filepath, mode)
        except Exception as e:
            logging.error(f"Failed to open file '{remote_filepath}': {e}")
            raise
