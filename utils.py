"""
    utils.py  
    Utility functions for Gambezi 

    Copyright (C) 2026 Clear Creek Scientific

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" 

import os
import requests
import zipfile


HTTP_PREFIX       = 'http'
LOCAL_FILE_PREFIX = 'file://'
DOCS_DIR          = 'docs'


def is_zipfile(path:str) -> bool:
    rv = False
    with open(path,'rb') as fd:
        buf = fd.read(2)
        if 0x50 == buf[0] and 0x4b == buf[1]:
            rv = True
    return rv

# Returns the path to the directory with the files
def download_http(src:str,dst:str,verbose:bool=False) -> int:
    rv = None
    try:
        r = requests.get(src)
        if r.status_code < 400:
            if r.headers['content-type'] == 'application/zip':
                filename = 'download.zip'
                if 'content-disposition' in r.headers:
                    s = r.headers['content-disposition']
                    parts = s.split(';')
                    for part in parts:
                        if part.strip().startswith('filename'):
                            subparts = part.split('=')
                            filename = subparts[1]
                dstdir = dst
                dst = os.path.join(dst,filename)
                with open(dst,'wb') as fd:
                    bytes_written = fd.write(r.content)
                if bytes_written == len(r.content):
                    print('Extracting: ' + str(dst))
                    with zipfile.ZipFile(dst) as zf:
                        info_list = zf.infolist()
                        root = info_list[0].filename
                        if root.endswith('/'):
                            zf.extractall(dstdir)
                            root = root[:-1]
                            rv = os.path.join(dstdir,root)
    except Exception as e:
        print('Error retrieving file over HTTP: ' + str(e))
    return rv

# Returns the path to the directory with the files
def download_local_file(src:str,dst:str,verbose:bool=False) -> int:
    rv = None 
    buf = b''
    with open(src,'rb') as fd:
        buf = fd.read()
    if len(buf) > 0:
        dstdir = dst
        filename = os.path.basename(src)
        dst = os.path.join(dstdir,filename)
        with open(dst,'wb') as fd:
            bytes_written = fd.write(buf)
        if bytes_written == len(buf):
            if is_zipfile(dst):
                print('Extracting: ' + str(dst))
                with zipfile.ZipFile(dst) as zf:
                    info_list = zf.infolist()
                    root = info_list[0].filename
                    if root.endswith('/'):
                        zf.extractall(dstdir)
                        root = root[:-1]
                        rv = os.path.join(dstdir,root)
    return rv

# Returns the path to the directory with the files
def download_file(src:str,dst:str,verbose:bool=False) -> int:
    if verbose:
        print('Downloading: ' + str(src) + ' to ' + str(dst))
    if src.startswith(HTTP_PREFIX):
        return download_http(src,dst,verbose)
    elif src.startswith(LOCAL_FILE_PREFIX):
        return download_local_file(src[len(LOCAL_FILE_PREFIX):],dst,verbose)


# Returns the path to the directory with the files (used to get directory without doing a download)
def find_download_dir(start:str) -> str:
    rv = None
    if os.path.isdir(start):
        files = os.listdir(start)
        if DOCS_DIR in files:
            rv = start 
        else:
            for f in files:
                if os.path.isdir(os.path.join(start,f)):
                    rv = find_download_dir(os.path.join(start,f))
    else:
        print('[find_download_dir] start is not a directory (' + start + ')')
    return rv

