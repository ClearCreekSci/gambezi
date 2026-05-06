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

MOD_SUFFIX        = 'mods'
MODULES_DIR       = 'modules'
DOCS_DIR          = 'docs'
UI_FILE           = 'ui.xml'
KEY_SUBTYPE       = 'subtype'
KEY_OBJECTS       = 'objects'

AFFIRMATIVE       = ['y','Y','yes','Yes','YES','t','true','True','TRUE']

class GambeziDownloadError(Exception):
    pass

class GambeziConfigureError(Exception):
    pass

class GambeziInvalidObject(Exception):
    pass

class UnknownMetaObject(Exception):
    pass

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

    def do_add(self,arg):
        'Add a component to the installation: i.e. add <module name>'
        print('FIXME: add')
        return False

    def do_remove(self,arg):
        'Remove a component from the installation: i.e. remove <id>'
        print('FIXME: remove')
        return False

    def do_reset(self,arg):
        'Reset the configuration context (clear cache etc.)'
        if True == os.path.exists(self.meta.staging):
            print('Deleting cache directory: ' + self.meta.staging)
            shutil.rmtree(self.meta.staging)
            os.makedirs(self.meta.staging,exist_ok=True)
        return False

    def parse_ui(self,metabase):
        dst = os.path.join(metabase.download_path,DOCS_DIR)
        dst = os.path.join(dst,UI_FILE)
        self.ui.parse_types(dst)
        self.ui.parse_ui(dst,metabase.name)
        self.fixup_structs()

    def parse_local_ui(self):
        dst = os.path.join('.',DOCS_DIR)
        dst = os.path.join(dst,UI_FILE)
        self.ui.parse_types(dst)

    def do_configure(self,arg):
        'Configure a component in the installation: i.e. configure logger'
        found = False
        for app in self.meta.apps:
            if app.name == arg:
                found = True
                if self.download_component(app):
                    self.parse_ui(app)
                    self.configure_app(app)
                else:
                    raise GambeziDownloadError('Error downloading ' + str(app.name))
                break
        #if False == found:
        #    for module in self.meta.modules:
        #        if module.name == arg:
        #            found = True
        #            if self.download_component(module):
        #                self.parse_ui(module)
        #                self.configure_uiconfig(module)
        #            else:
        #                raise GambeziDownloadError('Error downloading ' + str(module.name) + ': ' + str(e))
        #        break
        if False == found: 
            print('Cannot configure unknown element: ' + str(arg))
            print('The following are elements that may be configured:')
            print('Apps')
            print('----')
            for app in self.meta.apps:
                print('\t' + str(app.name))
            print('Modules')
            print('-------')
            for module in self.meta.modules:
                print('\t' + str(module.name))
        return False 

    def do_show(self,arg):
        'Show installation components and configuration'
        if None is not self.meta:
            print('Apps')
            print('--------------')
            if None is not self.meta.apps:
                for app in self.meta.apps:
                    s = '\t' + app.name
                    if None is not app.desc:
                        s += ' (' + app.desc + ')'
                    print(s)
            print('Modules')
            print('--------------')
            if None is not self.meta.modules:
                for module in self.meta.modules:
                    s = '\t' + module.name
                    if None is not module.desc:
                        s += ' (' + module.desc + ')'
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

    def download_component(self,v):
        dst = os.path.expanduser(os.path.join(self.meta.staging,v.name))
        self.check_file_cache(v,dst)
        if False == v.cached:
            os.makedirs(dst,exist_ok=True)
            dst = utils.download_file(v.url,dst,True)
            if dst is not None:
                v.download_path = dst
                v.cached = True
        else:
            v.download_path = utils.find_download_dir(dst)
            print('Skipping download, using cached files in ' + str(v.download_path))
        return True

    def configure_member(self,obj,mtype,key):
            done = False
            try:
                while False == done:
                    default = str(mtype.default)
                    if (key in obj.values):
                        default = obj.values[key]
                    print('Enter value for ' + mtype.name + ' (' + default + '): ') 
                    x = input()
                    # If they just hit enter, keep the current value 
                    if len(x) == 0:
                        x = default 
                    if mtype.type == ui_config.TYPE_INT or mtype.type == ui_config.TYPE_CHAR or mtype.type == ui_config.TYPE_BYTE:
                        x = int(x)
                    elif mtype.type == ui_config.TYPE_FLOAT:
                        x = float(x)
                    obj.values[key] = x 
                    done = True
            except Exception as e:
                s = 'Value entry error (' + mtype.name + '): ' + str(e) + '\n'
                s += mtype.name + ' has type: ' + str(mtype.type) + '\n'
                if None is not mtype.desc:
                    s += mtype.name + ' description: ' + mtype.desc + '\n'
                raise GambeziConfigureError(s)

    def configure_struct(self,obj,otype):
        for key in otype.members.keys():
            mtype = otype.members[key]
            if mtype.type in ui_config.BASE_TYPES:
                self.configure_member(obj,mtype,key)
            else:
                stype = self.ui.find_type(mtype.type)
                self.configure_struct(obj,stype)


    def configure_list(self,obj,otype):
        if False == isinstance(otype,ui_config.UiList):
            raise GambeziInvalidObject('Expected UiList, got ' + str(type(otype)))
        if False == KEY_OBJECTS in obj.values.keys():
            raise GambeziInvalidObject("Didn't find 'values' key in UiList")
        mtype = self.ui.find_type(otype.subtype)
        if None is mtype:
            raise GambeziInvalidObject("Didn't find subtype: " + otype.subtype)
        items = obj.values[KEY_OBJECTS]
        for item in items:
            current_obj = obj.values[item]
            current_obj_type = self.ui.find_type(current_obj.type)
            if ui_config.TYPE_STRUCT == current_obj_type.type:
                self.configure_struct(current_obj,current_obj_type)
            else:
                print('[configure_list] current_obj: ' + str(current_obj))
                print('[configure_list] current_obj_type: ' + str(current_obj_type))

    def configure_app(self,app):
        if app.name in self.ui.components.keys():
            for key in self.ui.components[app.name]:
                obj = self.ui.components[app.name][key]
                otype = self.ui.find_type(obj.type)
                if isinstance(otype,ui_config.UiStruct):
                    self.configure_struct(obj,otype)
                elif isinstance(otype,ui_config.UiList):
                    self.build_list(obj)
                    self.configure_list(obj,otype)
        else:
            raise GambeziConfigureError("Couldn't find UI configuration for " + app.name)

    def fixup_structs(self):
        print('[fixup_structs]')
        full_types = dict()
        for key in self.ui.types.keys():
            otype = self.ui.types[key]
            print('[fixup_structs] looking at ' + otype.name)
            if isinstance(otype,ui_config.UiStruct):
                print('[fixup_structs] fixing up ' + otype.name)
                x = self.build_full_type(otype)
                full_types[otype.name] = x
            else:
                print('[fixup_structs] appending ' + otype.name)
                full_types[otype.name] = otype
        self.ui.types = full_types

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
                    if False == self.download_component(app):
                        raise GambeziDownloadError('[2] Error downloading ' + str(app.name) + ': ' + str(e))
        return rv

    def build_list(self,obj):
        typelist = list()
        otype = self.ui.find_type(obj.type)
        # In the future, we may have other list items besides module names
        for module in self.meta.modules:
            search = module.loader + ':' + module.prefix
            if search == otype.subtype:
                typelist.append(module.name + ':' + module.prefix)
            else:
                super_types = self.ui.find_super_types(obj.type)
                for t in super_types:
                    if search == t.subtype:
                        typelist.append(module.name)
        done = False
        objlist = list()
        while False == done:
            for mod in typelist:
                print(mod)
            x = input('Add a module (y/n)? ')
            if x in AFFIRMATIVE:
                ok = False
                while ok == False:
                    mname = input('Please enter name: ')
                    if mname in typelist:
                        ok = True
                    else:
                        print(mname + ' is not a valid type. Please enter one of the following:')
                        for mod in typelist:
                            print(mod)
                mid = input('Please enter an ID for ' + mod + ': ')
                objlist.append(mname + '/' + mid)
                found = False
                basename = mod
                if ':' in basename:
                    parts = basename.split(':')
                    basename = parts[0]
                for module in self.meta.modules:
                    if module.name == basename:
                        found = True
                        if self.download_component(module):
                            self.parse_ui(module)
                            break;
                        else:
                            raise GambeziDownloadError('Error downloading ' + str(module.name))
                if False == found:
                    raise UnknownMetaObject("Couldn't find meta object named " + mod)
            else:
                done = True
        obj.values[KEY_SUBTYPE] = otype.subtype
        obj.values[KEY_OBJECTS] = objlist
        for o in objlist:
            obj.values[o] = ui_config.UiObject()
            # FIXME: We need to make this operation generic
            parts = o.split('/')
            t = o
            if 2 == len(parts):
                t = parts[0]
            obj.values[o].type = t

    def build_full_type(self,otype):
        rv = None
        if isinstance(otype,ui_config.UiStruct):
            rv = otype.clone()
            print('[build_full_type] otype: ' + str(otype))
            if len(otype.super_types) > 0:
                for super_name in otype.super_types:
                    t = self.ui.find_type(super_name)
                    for key in t.members.keys():
                        rv.members[key] = t.members[key].clone()             
            else:
                print('No super types')
        else:
            raise GambeziInvalidObject('Error trying to build full type for: ' + str(otype))
        return rv

    def check_file_cache(self,v,dst):
        if False == v.cached:
            if os.path.exists(dst):
                v.cached = True

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

