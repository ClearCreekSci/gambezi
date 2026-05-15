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

banner = '''
  ________              ___.                 .__ 
 /  _____/_____    _____\\_ |__   ____ _______|__|
/   \\  ___\\__  \\  /     \\| __ \\_/ __ \\\\___   /  |
\\    \\_\\  \\/ __ \\|  Y Y  \\ \\_\\ \\  ___/ /    /|  |
 \\______  (____  /__|_|  /___  /\\___  >_____ \\__|
        \\/     \\/      \\/    \\/     \\/      \\/   
'''

intro = '''
Gambezi is a command-line python program used to create installation bundles
for Clear Creek Scientific applications. It is not as easy to use as programs
with a graphical user interface, but it runs everywhere python does without
needing to install any additional libraries. To learn how to use Gambezi, type
"help" (without the quotes) at anytime to see the available commands.
'''

DEFAULT_META_PATH = './meta.xml'

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
            try:
                os.rmdir(dst)
            except Exception as e:
                print('Error removing cache directory (' + dst + '): ' + str(e))
            return False
    else:
        comp.download_path = utils.find_download_dir(dst)
        print('Skipping download, using cached files in ' + str(comp.download_path))
    return True

def configure_member(obj,mtype,key):
        done = False
        try:
            while False == done:
                default = ''
                if key in obj.defaults:
                    default = obj.defaults[key]
                if (key in obj.values):
                    default = obj.values[key]
                print('Enter value for ' + mtype.name + ' (' + str(default) + '): ')
                x = input()
                # If they just hit enter, keep the current value
                if len(x) == 0:
                    x = default

                print('[configure_member] setting ' + str(key) + ' to ' + str(x))

                obj.values[key] = x
                done = True
        except Exception as e:
            s = 'Value entry error (' + mtype.name + '): ' + str(e) + '\n'
            s += mtype.name + ' has type: ' + str(mtype.type) + '\n'
            if None is not mtype.desc:
                s += mtype.name + ' description: ' + mtype.desc + '\n'
            raise GambeziConfigureError(s)

def configure_struct(ui,obj,otype):
    for key in otype.members.keys():
        mtype = otype.members[key]
        if mtype.type in const.BASE_TYPES:
            if False == mtype.ignore:
                configure_member(obj,mtype,key)
        else:
            new_object = ui_config.UiObject() 
            new_object.name = key 
            new_object.type = otype.name
            # Copy all the defaults to each object because we don't know which
            # ones different members will require...
            for defkey in obj.defaults.keys():
                new_object.defaults[defkey] = obj.defaults[defkey]
            stype = ui.find_type(mtype.type)
            configure_struct(ui,new_object,stype)
            obj.values[key] = new_object 

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
        'Show list item types [show types] or list item values [show values]'
        if arg == 'types':
            print('Available types:')
            atypes = self.get_available_types()
            for atype in atypes:
                obj = self.ui.find_object_by_type(atype.name)
                print(obj.name)
        elif arg == 'values':
            print('Configured values:')
            for key in self.obj.values.keys():
                if const.TAG_SUBTYPE == key:
                    continue
                v = self.obj.values[key]
                print(key + ':\n')
                print(v)
        else:
            print('Unknown option: ' + str(arg))
            print('The available options are "types" or "values"')
        return False

    def do_add(self,arg):
        'Add a component to the list: i.e. add bme280'
        found = False
        atypes = self.get_available_types()
        for atype in atypes:
            obj = self.ui.find_object_by_type(atype.name)
            if None is not obj:
                if arg == obj.name:
                    mid = input('Please enter an ID for ' + arg + ': ')
                    full_name = arg + '/' + mid
                    if isinstance(atype,ui_config.UiStruct):
                        obj = obj.clone()
                        configure_struct(self.ui,obj,atype)
                        self.obj.values[full_name] = obj
                        found = True
                    else:
                        print('Trying to add invalid type (' + str(type(atype)) + ') to the application')
        if False == found:
            print('Unknown type: ' + arg)
            print('The following types are available:')
            for x in atypes:
                print(x.name)
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
        atypes = list()
        if const.TAG_SUBTYPE in self.obj.values.keys():
            subtype = self.obj.values[const.TAG_SUBTYPE]
            otype = self.ui.find_type(subtype)
            if None is not otype:
                if False == otype.abstract:
                    atypes.append(otype)
                subtype_names = self.ui.find_sub_types(otype.name)
                for subtype_name in subtype_names:
                    subtype = self.ui.find_type(subtype_name)
                    if (None is not subtype) and (False == subtype.abstract):
                        atypes.append(subtype)
        return atypes

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
                        configure_struct(self.ui,obj,otype)
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
                        configure_struct(self.ui,obj,otype)
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
        for comp_key in self.ui.components[self.name].keys():
            comp = self.ui.components[self.name][comp_key]
            if 0 == len(comp.values):
                for def_key in comp.defaults.keys():
                    comp.values[def_key] = comp.defaults[def_key]
        self.parent.set_ui(self.ui)
        for x in self.meta.apps:
            if x.name == self.name:
                x.configured = True
        return True

    def do_show(self,arg):
        'Show application objects that need configuring'
        for key in self.ui.components[self.name]:
            print(str(key))
            #print(str(self.ui.components[self.name][key]))

class CcsBuildInstaller(cmd.Cmd):
    prompt = 'build installer> '

    def __init__(self):
        super().__init__()
        self.meta = None
        self.ui = ui_config.UiConfig()

    # Returns True if everything is OK
    # Returns False if there is a problem
    def check_build(self):
        rv = True
        #print('[check_build] ui: ' + str(self.ui))
        for comp_key in self.ui.components.keys():
            #print('[check_build] comp_key: ' + str(comp_key))
            comp = self.ui.components[comp_key]
            if hasattr(comp,'configured') and comp.configured:
                for obj_key in self.ui.components[comp_key].keys():
                    obj = self.ui.components[comp_key][obj_key]
                    v = obj.values
                    if 0 == len(obj.values):
                        print("Can't build. Empty value found for " + str(obj.name))
                        rv = False
                    # if it has a 'subtype' tag, treat it as a list
                    elif const.TAG_SUBTYPE in v.keys():
                        # if the list doesn't have anything else in it 
                        if 1 == len(v.keys()):
                            print("Can't build. Empty list found for " + str(obj.name))
                            rv = False
        return rv

    def build_it(self):
        if None is not self.meta.apps:
            for app in self.meta.apps:
                if app.configured:
                    path = os.path.join(app.download_path,const.SETTINGS_FILE_NAME)
                    self.write_app_settings(app,path)

    def do_build(self,arg):
        'Build the installer'
        if True == self.check_build():
            self.build_it()
        return False 

    def do_reset(self,arg):
        'Reset the configuration context (clear cache etc.)'
        if True == os.path.exists(self.meta.staging):
            print('Deleting cache directory: ' + self.meta.staging)
            shutil.rmtree(self.meta.staging)
            os.makedirs(self.meta.staging,exist_ok=True)
        print('Resetting cached values')
        for app in self.meta.apps:
            app.cached = False
            app.configured = False
        for mod in self.meta.modules:
            mod.cached = False
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
            print('----')
            if None is not self.meta.apps:
                for app in self.meta.apps:
                    s = '\t' + app.name
                    if None is not app.desc:
                        s += ' (' + app.desc + ')'
                    print(s)
        return False 

    def do_tutorial(self,arg):
        'Displays a short tutorial on how to use gambezi'
        print("\nThe 'show' command will show the apps that can be configured")
        print("For example:")
        print('build_installer> show')
        print('Apps')
        print('----')
        print('\tlogger (Collect and store data from sensors)')
        print('\tserver (Display collected data in a web browser)')
        if utils.should_quit("[press 'q' to quit, any other key to continue]"):
            return False
        print("\nThe 'configure' command requires the name of one of the apps")
        print("displayed by the 'show' command. Typing 'configure' followed")
        print("by an app name will start the configuration process for that")
        print("app. For example:")
        print('build_installer> configure logger')
        print('logger>')
        #if utils.should_quit("[press 'q' to quit, any other key to continue]"):
        #    return False
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

    def write_settings_list(self,obj,fd):
        if None is not obj.values:
            if False == const.TAG_SUBTYPE in obj.values.keys():
                # FIXME: throw an exception?
                return
            name = obj.name
            subname = obj.values[const.TAG_SUBTYPE]
            subtype = self.ui.find_type(subname)
            fd.write('<' + name + '>\n')
            for key in obj.values.keys():
                if key == const.TAG_SUBTYPE:
                    continue
                subobj = obj.values[key]
                if isinstance(subtype,ui_config.UiStruct):
                    self.write_settings_struct(subobj,fd,subtype.name) 
                elif isinstance(subtype,ui_config.UiList):
                    self.write_settings_list(subobj,fd)
                else:
                    print('[write_settings_list] ????????????????????')
            fd.write('</' + name + '>\n')

    # The 'name' parameter needs a little explanation. It is currently only
    # used when calling write_settings_struct from write_settings_list. By
    # setting 'name' to the list's subtype name, each object in the list
    # will get a surrounding tag with the subtype name.
    def write_settings_struct(self,obj,fd,name=None):
        write_extra_name = False
        if None is name:
            name = obj.name
        else:
            name = utils.get_simple_name(name)
            write_extra_name = True
        fd.write('<' + name + '>\n')

        if write_extra_name:
            fd.write('<name>')
            fd.write(obj.name)
            fd.write('</name>\n')
        for key in obj.values.keys():
            member = obj.values[key]
            if isinstance(member,ui_config.UiObject):
                self.write_settings_struct(member,fd)
            else:
                fd.write('<' + key + '>\n')
                fd.write(str(member) + '\n')
                fd.write('</' + key + '>\n')
        fd.write('</' + name + '>\n')

    def write_app_settings(self,app,path):
        print('Writing settings.cfg for ' + str(app.name) + ' (' + path + ')')
        with open(path,'wt') as fd:
            fd.write(const.XML_PREFIX + '\n')
            fd.write('<' + TAG_CONFIG_ROOT + ' ' + ATTRIB_VERSION + CONFIG_VERSION + '>\n')
            for key in self.ui.components[app.name].keys():
                obj = self.ui.components[app.name][key]
                otype = self.ui.find_type(obj.type)
                if isinstance(otype,ui_config.UiStruct):
                    self.write_settings_struct(obj,fd) 
                elif isinstance(otype,ui_config.UiList):
                    self.write_settings_list(obj,fd)
                else:
                    print('[write_app_settings] ????????????????????')
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
    print(banner)
    print(intro)
    try:
        build_installer = CcsBuildInstaller()
        build_installer.parse_metadata(DEFAULT_META_PATH)
        build_installer.parse_local_ui()
        # build_installer.do_help('')
        build_installer.cmdloop()
    except Exception as e:
        print(traceback.format_exc())
        print('Exception: ' + str(type(e)))
        print('[__main__] ' + str(e))
        traceback.print_stack()

