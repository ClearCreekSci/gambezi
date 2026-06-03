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

import const

HTTP_PREFIX       = 'http'
LOCAL_FILE_PREFIX = 'file://'

class GambeziDownloadError(Exception):
    pass

class GambeziConfigureError(Exception):
    pass

class GambeziInvalidObject(Exception):
    pass

class UnknownMetaObject(Exception):
    pass

class InvalidGambeziMetaFile(Exception):
    pass

class InvalidGambeziMetaEntry(Exception):
    pass

class InvalidUiConfigElement(Exception):
    pass

class InvalidCcsUiFile(Exception):
    pass

def is_zipfile(path:str) -> bool:
    rv = False
    with open(path,'rb') as fd:
        buf = fd.read(2)
        if 0x50 == buf[0] and 0x4b == buf[1]:
            rv = True
    return rv

def get_commit(url):
    rv = None
    try:
        r = requests.get(url)
        if r.status_code < 400:
            if r.headers['content-type'].startswith('text/html'):
                x = r.content.decode('utf-8')
                head = x.find(const.COMMIT_MARKER) + len(const.COMMIT_MARKER)
                if head > 0:
                    while x[head] in const.WHITESPACE:
                        head += 1
                    if x[head:].startswith(const.COMMIT_URL_MARKER):
                        head += len(const.COMMIT_URL_MARKER)
                        while False == x[head:].startswith('href'):
                            head += 1
                        head += len('href')
                        while '"' != x[head]:
                            head += 1
                        head += 1
                        tail = head
                        while '"' != x[tail]:
                            tail += 1
                        url = x[head:tail]
                        parts = url.split('/')
                        rv = parts[len(parts)-1]
                    else:
                        print("[!] Couldn't find commit number in downloaded file:" + str(url))
        else:
            print('[!] Error (' + str(r.status_code) + ') retrieving commit meta file: ' + str(url))
    except Exception as e:
        print('[!] Error getting app commit number from ' + str(url) + ': ' + str(e))
    return rv

# Returns the path to the directory with the "docs" dir 
def find_download_dir(start:str,depth:int) -> str:
    rv = None
    if os.path.isdir(start):
        files = os.listdir(start)
        if const.DOCS_DIR in files:
            rv = start 
        else:
            for f in files:
                check_path = os.path.join(start,f)
                if os.path.isdir(check_path):
                    rv = find_download_dir(check_path,depth+1)
                    if None is not rv:
                        break
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

def download_component(stage,comp):

    if None is comp:
        print('[download_component: comp is NULL!')
        return const.DOWNLOAD_FAILED 
    rv = const.DOWNLOAD_COMPLETED
    # Look for base path
    dst = os.path.expanduser(os.path.join(stage,comp.name))
    check_file_cache(comp,dst)
    if False == comp.cached:
        # Create base path
        os.makedirs(dst,exist_ok=True)
        # Get real download path
        downloaded = download_file(comp.url,dst,True)
        if downloaded is not None:
            comp.download_path = downloaded
            comp.cached = True
        else:
            try:
                os.rmdir(dst)
            except Exception as e:
                print('Error removing cache directory (' + dst + '): ' + str(e))
            rv = const.DOWNLOAD_FAILED
    else:
        comp.download_path = find_download_dir(dst,0)
        print('Skipping download, using cached files in ' + str(comp.download_path))
        rv = const.DOWNLOAD_SKIPPED
    return rv

def check_file_cache(v,dst):
    if False == v.cached:
        if os.path.exists(dst):
            v.cached = True

def get_simple_name(s):
    rv = s
    parts = s.split(':')
    if len(parts) == 2:
        rv = parts[1]
    return rv

def get_namespace(s):
    rv = s
    parts = s.split(':')
    if len(parts) == 2:
        rv = parts[0]
    return rv


def should_quit(msg):
    print('')
    x = input(msg)
    return x == 'q'


