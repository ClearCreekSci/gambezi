"""
    gambezi.py
    Interface for CCS data logger and server configuration

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
import cmd
import sys
import shutil
import traceback

import const
import metadata
import ui_config
import utils

intro = '''
  ________              ___.                 .__ 
 /  _____/_____    _____\\_ |__   ____ _______|__|
/   \\  ___\\__  \\  /     \\| __ \\_/ __ \\\\___   /  |
\\    \\_\\  \\/ __ \\|  Y Y  \\ \\_\\ \\  ___/ /    /|  |
 \\______  (____  /__|_|  /___  /\\___  >_____ \\__|
        \\/     \\/      \\/    \\/     \\/      \\/   
'''

DEFAULT_META_PATH = './meta.xml'

XML_PREFIX        = '<?xml version="1.0" encoding="UTF-8"?>'
TAG_CONFIG_ROOT   = 'ccs-config'
ATTRIB_VERSION    = 'version='
CONFIG_VERSION    = '"2"'

def build_full_type(ui,otype):
    rv = None
    if isinstance(otype,ui_config.UiStruct):
        rv = otype.clone()
        if len(otype.super_types) > 0:
            for super_name in otype.super_types:
                t = ui.find_type(super_name)
                for key in t.members.keys():
                    rv.members[key] = t.members[key].clone()             
    else:
        raise utils.GambeziInvalidObject('Error trying to build full type for: ' + str(otype))
    return rv

def fixup_structs(ui):
    full_types = dict()
    for key in ui.types.keys():
        otype = ui.types[key]
        if isinstance(otype,ui_config.UiStruct):
            x = build_full_type(ui,otype)
            full_types[otype.name] = x
        else:
            full_types[otype.name] = otype
    ui.types = full_types

def parse_ui(metabase,ui,comp):
    dst = os.path.join(comp.download_path,const.DOCS_DIR)
    dst = os.path.join(dst,const.UI_FILE)
    ui.parse_types(dst)
    ui.parse_ui(dst,comp.name)
    fixup_structs(ui)

def download_app_modules(meta,ui,app):
    dst = os.path.expanduser(os.path.join(meta.staging,app.name))
    for x in meta.modules:
        if x.loader == app.name:
            download_component(meta.staging,x)
            parse_ui(meta,ui,x)

def download_component(stage,comp):
    # Look for base path
    dst = os.path.expanduser(os.path.join(stage,comp.name))
    utils.check_file_cache(comp,dst)
    if False == comp.cached:
        # Create base path
        os.makedirs(dst,exist_ok=True)
        # Get real download path
        downloaded = utils.download_file(comp.url,dst,True)
        if downloaded is not None:
            comp.download_path = downloaded
            comp.cached = True
        else:
            #try:
            os.rmdir(dst)
            #except Exception:
            #    pass
            return False
    else:
        comp.download_path = utils.find_download_dir(dst)
        print('Skipping download, using cached files in ' + str(comp.download_path))
    return True

class CcsListConfigurator(cmd.Cmd):
    prompt = '> '

    def __init__(self):
        super().__init__()
        self.list_name = None
        self.ui = None
        self.obj = None

    def setup(self,app,list_name):
        self.app = app
        self.ui = app.ui.clone()
        self.list_name = list_name
        self.prompt = list_name + '> '
        self.obj = self.ui.find_object_by_name(app.name,list_name)

    def do_cancel(self,arg):
        'Cancel list configuration and return to application configuration'
        print('Return to app configuration without saving list? (y/n)')
        x = input()
        if x in const.AFFIRMATIVE:
            return True
        return False

    def do_show(self,arg):
        'Show list configuration'
        print('Available types:')
        type_names = self.get_available_types()
        for type_name in type_names:
            print(type_name)
        print('----------------------------------------')
        print('Configured values:')
        for key in self.obj.values.keys():
            if const.TAG_SUBTYPE == key:
                continue
            v = self.obj.values[key]
        return False

    def do_add(self,arg):
        'Add a component to the list: i.e. add bme280:sensor'
        available_types = self.get_available_types()
        if arg in available_types:
            mid = input('Please enter an ID for ' + arg + ': ')
            full_name = arg + '/' + mid
            otype = self.ui.find_type(arg)
            if None is not otype:
                if isinstance(otype,ui_config.UiStruct):
                    parts = arg.split(':')
                    obj = self.ui.find_object_by_type(parts[0],arg)
                    if None is not obj:
                        utils.configure_struct(self.ui,obj,otype)
                        self.obj.values[full_name] = obj
                    else:
                        print("Couldn't find obj: " + parts[0])
            else:
                print("Couldn't find type: " + arg)
        else:
            print('Unknown type: ' + arg)
            print('The following types are available:')
            for x in available_types:
                print(x)
        return False

    def do_remove(self,arg):
        'Remove a component from the list: i.e. remove <id>'
        print('FIXME: do_remove')
        return False

    def do_save(self,arg):
        'Save the current list and return to app configuration.'
        print('Saving list and returning to app configuration')
        self.app.ui = self.ui
        return True

    def get_available_types(self):
        type_names = list()
        if const.TAG_SUBTYPE in self.obj.values.keys():
            subtype = self.obj.values[const.TAG_SUBTYPE]
            otype = self.ui.find_type(subtype)
            if None is not otype:
                if False == otype.abstract:
                    type_names.append(otype.name)
                subtype_names = self.ui.find_sub_types(otype.name)
                for subtype_name in subtype_names:
                    subtype = self.ui.find_type(subtype_name)
                    parts = subtype.name.split()
                    subtype_name = parts[0]
                    if False == subtype.abstract:
                        type_names.append(subtype_name)
        return type_names

class CcsAppConfigurator(cmd.Cmd):
    prompt = '> '

    def __init__(self):
        super().__init__()
        self.meta = None
        self.ui = None

    def setup(self,parent,name):
        self.meta = parent.meta
        self.ui = parent.ui.clone()
        self.parent = parent
        self.name = name
        self.prompt = name + '> '
        app = None
        for x in self.meta.apps:
            if x.name == name:
                app = x
        if None is not app:
            download_app_modules(self.meta,self.ui,app)

    def do_cancel(self,arg):
        'Cancel app configuration and return to install builder.'
        print('Return to install builder without saving app configuration? (y/n)')
        x = input()
        if x in const.AFFIRMATIVE:
            return True
        return False

    def do_set(self,arg):
        'Set values for the currently selected application in the installation'
        arg = arg.strip()
        if None is arg or 0 == len(arg):
            if self.name in self.ui.components.keys():
                for key in self.ui.components[self.name]:
                    obj = self.ui.components[self.name][key]
                    otype = self.ui.find_type(obj.type)
                    if isinstance(otype,ui_config.UiStruct):
                        utils.configure_struct(self.ui,obj,otype)
                    elif isinstance(otype,ui_config.UiList):
                        list_config = CcsListConfigurator()
                        list_config.setup(self,obj.name)
                        list_config.cmdloop()
                
            else:
                raise utils.GambeziConfigureError("Couldn't find UI configuration for " + self.name)
        else:
            found = False
            for key in self.ui.components[self.name]:
                if key == arg:
                    obj = self.ui.components[self.name][key]
                    otype = self.ui.find_type(obj.type)
                    if isinstance(otype,ui_config.UiStruct):
                        utils.configure_struct(self.ui,obj,otype)
                    elif isinstance(otype,ui_config.UiList):
                        list_config = CcsListConfigurator()
                        list_config.setup(self,obj.name)
                        list_config.cmdloop()
                    found = True
            if False == found:
                print('Unknown component (' + arg + ')')
                print('The following components are available:')
                for key in self.ui.components[self.name]:
                    print(key) 
        return False


    def do_save(self,arg):
        'Save the current app configuration and return to install builder.'
        print('Saving configuration and returning to install builder')
        self.parent.set_ui(self.ui)
        return True

    def do_show(self,arg):
        'Show application objects that need configuring'
        for key in self.ui.components[self.name]:
            print(str(key)) 
            print(str(self.ui.components[self.name][key]))

class CcsBuildInstaller(cmd.Cmd):
    prompt = 'build installer> '

    def __init__(self):
        super().__init__()
        self.ui = ui_config.UiConfig()

    def check_build(self):
        print('FIXME: Check to see if the build makes sense.')
        print('For example:')
        print('Check to see if any lists are empty. (list items are added by modules?)')
        print('Check to see if the modules have conflicting settings (are we making this configurable)?')
        print('etc.')

    def build_it(self):
        print('FIXME: build_it')

    def do_build(self,arg):
        'Build the installer'
        self.check_build()
        self.build_it()
        return False 

    def do_reset(self,arg):
        'Reset the configuration context (clear cache etc.)'
        if True == os.path.exists(self.meta.staging):
            print('Deleting cache directory: ' + self.meta.staging)
            shutil.rmtree(self.meta.staging)
            os.makedirs(self.meta.staging,exist_ok=True)
        for x in self.ui.components:
            x.cached = False
        return False

    def parse_local_ui(self):
        dst = os.path.join('.',const.DOCS_DIR)
        dst = os.path.join(dst,const.UI_FILE)
        self.ui.parse_types(dst)

    def do_configure(self,arg):
        'Configure an application in the installation: i.e. configure logger'
        found = False
        for app in self.meta.apps:
            if app.name == arg:
                found = True
                if download_component(self.meta.staging,app):
                    parse_ui(self.meta,self.ui,app)
                    self.configure_app(app)
                else:
                    print('Error downloading ' + str(app.name))
                break
        if False == found:
            print('Cannot configure unknown element: ' + str(arg))
            print('The following are elements that may be configured:')
            print('Apps')
            print('----')
            for app in self.meta.apps:
                print('\t' + str(app.name))
        return False

    def do_show(self,arg):
        'Show applications available for configuration'
        if None is not self.meta:
            print('Apps')
            print('--------------')
            if None is not self.meta.apps:
                for app in self.meta.apps:
                    s = '\t' + app.name
                    if None is not app.desc:
                        s += ' (' + app.desc + ')'
                    print(s)
        return False 

    def do_quit(self,arg):
        'Quit the program'
        return True

    def parse_metadata(self,path):
        self.meta = metadata.GambeziMeta()
        try:
            self.meta.read(path)
            if self.meta.staging is None:
                raise utils.InvalidGambeziMetaFile('Metadata null staging path encountered')
            for app in self.meta.apps:
                if False == hasattr(app,'name') or None is app.name:
                    raise utils.InvalidGambeziMetaFile('App null name encountered')
                if False == hasattr(app,'url') or None is app.url:
                    raise utils.InvalidGambeziMetaFile('App (' + str(app.name) + ') null url encountered')
        except Exception as e:
            print('[parse_metadata] Error parsing metadata: ' + str(e))

    def configure_app(self,app):
        app_config = CcsAppConfigurator()
        app_config.setup(self,app.name)
        app_config.cmdloop()
        #print('[configure_app] configuration finished...')
        #print(self.ui)

    def write_app_settings(self,app,path):
        print('Writing settings.cfg for ' + str(app.name) + ' (' + path + ')')
        with open(path,'wt') as fd:
            fd.write(XML_PREFIX + '\n')
            fd.write('<' + TAG_CONFIG_ROOT + ' ' + ATTRIB_VERSION + CONFIG_VERSION + '>\n')
            for key in self.ui.components[app.name].keys():
                obj = self.ui.components[app.name][key]
                otype = app.ui_types.find_type(obj.type)
                if isinstance(otype,ui_config.UiStruct):
                    name = app.ui_types.get_name(obj.type)
                    fd.write('<' + name + '>\n')
                    for key in otype.members.keys():
                        member = otype.members[key]
                        fd.write('<' + member.name + '>\n')
                        fd.write(str(member.default) + '\n')
                        fd.write('</' + member.name + '>\n')
                    fd.write('</' + name + '>\n')
                elif isinstance(otype,ui_config.UiList):
                    # FIXME: This is all kinds of broken...
                    #stype = app.ui_config.find_type(obj.type)
                    name = app.ui_types.get_name(obj.type)
                    fd.write('<' + name + '>\n')
                    #for key in stype.members.keys():
                    #    fd.write('<' + stype.name + '>\n')
                    #    fd.write(str(stype.members))
                    #    fd.write('</' + stype.name + '>\n')
                    fd.write('</' + name + '>\n')
            fd.write('</' + TAG_CONFIG_ROOT + '>\n')

    def get_loader_app(self,name):
        rv = None
        for app in self.meta.apps:
            if app.name == name:
                rv = app
                if False == app.cached:
                    if False == download_component(self.meta.staging,app):
                        raise utils.GambeziDownloadError('[2] Error downloading ' + str(app.name) + ': ' + str(e))
        return rv

    def set_ui(self,ui):
        self.ui = ui

if '__main__' == __name__:
    print(intro)
    try:
        build_installer = CcsBuildInstaller()
        build_installer.parse_metadata(DEFAULT_META_PATH)
        build_installer.parse_local_ui()
        build_installer.do_help('')
        build_installer.cmdloop()
    except Exception as e:
        print(traceback.format_exc())
        print('Exception: ' + str(type(e)))
        print('[__main__] ' + str(e))
        traceback.print_stack()

