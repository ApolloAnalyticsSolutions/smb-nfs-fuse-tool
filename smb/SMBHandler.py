import os
import sys
import socket
import urllib.request
import urllib.error
import urllib.parse
import mimetypes
import email
import tempfile
from urllib.parse import (
    unwrap, unquote, splittype, splithost, quote,
    splitport, splittag, splitattr, splituser, splitpasswd, splitvalue
)
from urllib.response import addinfourl
from nmb.NetBIOS import NetBIOS
from smb.SMBConnection import SMBConnection
from io import BytesIO

USE_NTLM = True
MACHINE_NAME = None

class SMBHandler(urllib.request.BaseHandler):
    def smb_open(self, req):
        """
        Open an SMB connection and handle the request.
        """
        global USE_NTLM, MACHINE_NAME

        if not req.host:
            raise urllib.error.URLError('SMB error: no host given')
        
        host, port = splitport(req.host)
        port = int(port) if port else 139

        # Username/password handling
        user, host = splituser(host)
        passwd = None
        
        if user:
            user, passwd = splitpasswd(user)
        
        host = unquote(host)
        user = user or ''
        passwd = passwd or ''

        domain = ''
        if ';' in user:
            domain, user = user.split(';', 1)

        myname = MACHINE_NAME or self.generateClientMachineName()

        server_name, host = host.split(',') if ',' in host else (None, host)

        if server_name is None:
            n = NetBIOS()
            names = n.queryIPForName(host)
            if names:
                server_name = names[0]
            else:
                raise urllib.error.URLError('SMB error: Hostname does not reply back with its machine name')

        path, attrs = splitattr(req.selector)
        if path.startswith('/'):
            path = path[1:]
        dirs = list(map(unquote, path.split('/')))
        service, path = dirs[0], '/'.join(dirs[1:])

        try:
            conn = SMBConnection(user, passwd, myname, server_name, domain=domain, use_ntlm_v2=USE_NTLM)
            conn.connect(host, port)

            headers = email.message.Message()
            if req.data:
                conn.storeFile(service, path, req.data)
                headers.add_header('Content-length', '0')
                fp = BytesIO(b"")
            else:
                fp = self.createTempFile()
                file_attrs, retrlen = conn.retrieveFile(service, path, fp)
                fp.seek(0)
                mtype = mimetypes.guess_type(req.get_full_url())[0]
                if mtype:
                    headers.add_header('Content-type', mtype)
                if retrlen is not None and retrlen >= 0:
                    headers.add_header('Content-length', '%d' % retrlen)

            return addinfourl(fp, headers, req.get_full_url())
        except Exception as ex:
            raise urllib.error.URLError(f'SMB error: {ex}').with_traceback(sys.exc_info()[2])

    @staticmethod
    def createTempFile():
        """
        Create a temporary file.
        """
        return tempfile.TemporaryFile()

    @staticmethod
    def generateClientMachineName():
        """
        Generate a client machine name based on the hostname or process ID.
        """
        hostname = socket.gethostname()
        return hostname.split('.')[0] if hostname else f'SMB{os.getpid()}'
