'''
    manifest.py
    Records data from various sensors

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
import datetime as dt
import xml.etree.ElementTree as et

XML_PREFIX         = '<?xml version="1.0" encoding="UTF-8"?>'
TAG_TIME           = 'time'
TAG_COMMIT         = 'commit'
TAG_MANIFEST       = 'manifest'
TAG_VERSION        = 'version'
# Name is optional
TAG_NAME           = 'name'

class Manifest(object):

    def __init__(self):
        self.time = ''
        self.commit = ''
        self.version = ''
        self.name = None

    def read(self,path):
        tree = et.parse(path)
        root = tree.getroot()
        for child in root:
            if child.tag == TAG_TIME:
                self.time = child.text.strip()
            elif child.tag == TAG_COMMIT:
                self.commit = child.text.strip()
            elif child.tag == TAG_VERSION:
                self.version = child.text.strip()
            elif child.tag == TAG_NAME:
                self.name = child.text.strip()

    def write(self,path):
        with open(path,'wt') as fd:
            fd.write(XML_PREFIX + '\n')
            fd.write('<' + TAG_MANIFEST + '>\n')
            current_time = dt.datetime.now(dt.timezone.utc).isoformat(timespec='minutes')
            fd.write('<' + TAG_TIME + '>' + str(current_time) + '</' + TAG_TIME + '>\n')
            fd.write('<' + TAG_COMMIT + '>' + str(self.commit) + '</' + TAG_COMMIT + '>\n')
            fd.write('<' + TAG_VERSION + '>' + str(self.version) + '</' + TAG_VERSION + '>\n')
            if None is not self.name:
                fd.write('<' + TAG_NAME + '>' + str(self.name) + '</' + TAG_NAME + '>\n')
            fd.write('</' + TAG_MANIFEST + '>\n')



