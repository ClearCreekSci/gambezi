"""
    meta.py  
    Meta information for Gambezi 

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
import xml.etree.ElementTree as et

import utils
import ui_config

ATTRIB_NAME   = 'name'

TAG_APP       = 'app'
TAG_APPS      = 'apps'
TAG_DESC      = 'desc'
TAG_GAMBEZI   = 'gambezi'
TAG_LOADER    = 'loader'
TAG_MODULE    = 'module'
TAG_MODULES   = 'modules'
TAG_PATHS     = 'paths'
TAG_PREFIX    = 'prefix'
TAG_STAGING   = 'staging'
TAG_UICONFIG  = 'ui-config'
TAG_URL       = 'url'

class InvalidGambeziMetaFile(Exception):
    pass

class InvalidGambeziMetaEntry(Exception):
    pass

class MetaBase(object):

    def __init__(self):
        self.name = None
        self.url = None
        self.desc = None
        self.cached = False
        self.download_path = None
        self.meta = None
        self.loader = None

class MetaApp(MetaBase):

    def __init__(self):
        super().__init__()
        self.loader = 'self'

    def __repr__(self):
        s = 'MetaApp\n'
        s += 'name: ' + self.name + '\n'
        s += 'url: ' + self.url + '\n'
        s += 'desc: ' + self.desc + '\n'
        return s

class MetaModule(MetaBase):

    def __init__(self):
        super().__init__()
        self.prefix = '' 

    def __repr__(self):
        s = 'MetaModule\n'
        s += 'name: ' + self.name + '\n'
        s += 'url: ' + self.url + '\n'
        s += 'desc: ' + self.desc + '\n'
        s += 'loader: ' + str(self.loader) + '\n'
        s += 'prefix: ' + str(self.prefix) + '\n'
        return s

class GambeziMeta(object):

    def __init__(self):
        self.apps = list()
        self.modules = list()
        self.staging = None

    def read(self,path): 
        if os.path.exists(path):
            tree = et.parse(path)
            root = tree.getroot()
            if root.tag != TAG_GAMBEZI:
                raise InvalidGambeziMetaFile("Unrecognized root tag: " + root.tag)
            for paths_node in root.findall(TAG_PATHS):
                staging_node = paths_node.find(TAG_STAGING)
                if None is not TAG_STAGING:
                    self.staging = staging_node.text.strip()
            apps_node = root.find(TAG_APPS)
            for app_node in apps_node.findall(TAG_APP):
                app = MetaApp()
                if ATTRIB_NAME in app_node.attrib:
                    app.name = app_node.attrib[ATTRIB_NAME]
                url_node = app_node.find(TAG_URL);
                if None is not url_node:
                    app.url = url_node.text.strip()     
                desc_node = app_node.find(TAG_DESC);
                if None is not desc_node:
                    app.desc = desc_node.text.strip()     
                self.apps.append(app)
            modules_node = root.find(TAG_MODULES)
            for module_node in modules_node.findall(TAG_MODULE):
                module = MetaModule()
                if ATTRIB_NAME in module_node.attrib:
                    module.name = module_node.attrib[ATTRIB_NAME]
                else:
                    raise InvalidGambeziMetaEntry('Module is missing name value')
                url_node = module_node.find(TAG_URL);
                if None is not url_node:
                    module.url = url_node.text.strip()     
                else:
                    raise InvalidGambeziMetaEntry('Module (' + module.name + ') is missing url value')
                desc_node = module_node.find(TAG_DESC);
                if None is not desc_node:
                    module.desc = desc_node.text.strip()     
                loader_node = module_node.find(TAG_LOADER);
                if None is not loader_node:
                    module.loader = loader_node.text.strip()     
                else:
                    raise InvalidGambeziMetaEntry('Module (' + module.name + ') is missing loader value')
                prefix_node = module_node.find(TAG_PREFIX);
                if None is not prefix_node:
                    module.prefix = prefix_node.text.strip()     
                self.modules.append(module)
        else:
            raise FileNotFoundError("Couldn't find meta file: " + path)

