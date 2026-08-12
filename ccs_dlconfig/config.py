'''
    config.py
    Configuration for recording data from various sensors

    Copyright (C) 2025 Clear Creek Scientific

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
'''

import os
import xml.etree.ElementTree as et

TAG_BASE           = 'base'
TAG_CSV            = 'csv'
TAG_LOG            = 'log'
TAG_METRIC         = 'metric'
TAG_PATHS          = 'paths'
TAG_PHOTOS         = 'photos'
TAG_ROOT           = 'ccs-config'
TAG_VERSION        = 'version'
TAG_VIDEOS         = 'videos'

DEFAULT_BASE_DIR   = '.'
DEFAULT_CSV_DIR    = './csv'
DEFAULT_LOG_DIR    = './log'
DEFAULT_PHOTOS_DIR = './photos'
DEFAULT_VIDEOS_DIR = './videos'
DEFAULT_VERSION    = '2'

XML_DECL = '<?xml version="1.0" encoding="UTF-8"?>'

class Settings(object):
    
    def __init__(self):
        self.base_dir = DEFAULT_BASE_DIR
        self.csv_dir = DEFAULT_CSV_DIR
        self.log_dir = DEFAULT_LOG_DIR
        self.photos_dir = DEFAULT_PHOTOS_DIR
        self.videos_dir = DEFAULT_VIDEOS_DIR
        self.tree = None
        self.root = None
        self.version = None

    def set_base_dir(self,v):
        self.base_dir = v

    def set_csv_dir(self,v):
        self.csv_dir = v

    def set_log_dir(self,v):
        self.log_dir = v

    def read(self,path):
        if os.path.exists(path):
            self.tree = et.parse(path)
            self.root = self.tree.getroot()
            if TAG_VERSION in self.root.attrib: 
                self.version = int(self.root.attrib['version'].strip())
            for path in self.root.findall(TAG_PATHS):
                base = path.find(TAG_BASE)
                if None is not base:
                    self.base_dir = base.text.strip()
                else:
                    self.base_dir = None
                csv = path.find(TAG_CSV)
                if None is not csv:
                    self.csv_dir = csv.text.strip()
                else:
                    self.csv_dir = None
                log = path.find(TAG_LOG)
                if None is not log:
                    self.log_dir = log.text.strip()
                else:
                    self.log_dir = None
                photos = path.find(TAG_PHOTOS)
                if None is not photos:
                    self.photos_dir = photos.text.strip()
                else:
                    self.photos_dir = None
                videos = path.find(TAG_VIDEOS)
                if None is not videos:
                    self.videos_dir = videos.text.strip()
                else:
                    self.videos_dir = None
        else:
            raise FileNotFoundError("Couldn't find file: " + path)

    
    def write_prefix(self,fd):
            fd.write(XML_DECL + '\n')
            fd.write('<' + TAG_ROOT + ' ' + TAG_VERSION + '="' + DEFAULT_VERSION + '">\n')
            fd.write('<' + TAG_PATHS + '>\n')
            if None is not self.base_dir:
                fd.write('<' + TAG_BASE + '>' + self.base_dir + '</' + TAG_BASE + '>\n')
            if None is not self.log_dir:
                fd.write('<' + TAG_LOG + '>' + self.log_dir + '</' + TAG_LOG + '>\n')
            if None is not self.csv_dir:
                fd.write('<' + TAG_CSV + '>' + self.csv_dir + '</' + TAG_CSV + '>\n')
            if None is not self.photos_dir:
                fd.write('<' + TAG_PHOTOS + '>' + self.photos_dir + '</' + TAG_PHOTOS + '>\n')
            if None is not self.videos_dir:
                fd.write('<' + TAG_VIDEOS + '>' + self.videos_dir + '</' + TAG_VIDEOS + '>\n')
            fd.write('</' + TAG_PATHS + '>\n')

    def write_suffix(self,fd):
        fd.write('</' + TAG_ROOT + '>\n')

    def write(self,path):
        with open(path,'wt') as fd:
            self.write_prefix(fd)
            self.write_suffix(fd)

    def __repr__(self):
        s = TAG_VERSION + ' = ' + str(self.version) + '\n'
        s += TAG_BASE + ' = ' + str(self.base_dir) + '\n'
        s += TAG_LOG + ' = ' + str(self.log_dir) + '\n'
        s += TAG_CSV + ' = ' + str(self.csv_dir) + '\n'
        s += TAG_PHOTOS + ' = ' + str(self.photos_dir) + '\n'
        s += TAG_VIDEOS + ' = ' + str(self.videos_dir) + '\n'
        return s


