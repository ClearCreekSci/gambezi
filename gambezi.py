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
import random
import sys
import shutil
import stat
import subprocess
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

intros = list()
intros.append('Proceed. Not sure how?\nThe answer lies in the keys\nEnter help and read')
intros.append('Named after a fish\nThe interface is clunky\nStill, very useful')
intros.append('Only needs Python\nNothing else to install\nConfigure with joy')
intros.append('Greeted with sadness\nWhy is it not on the web?\nIt gets the job done')
intros.append('Command line Python?\nWhere is the WYSIWYG?\nOld school rules apply')
intros.append('Green phosphor on black\nLate nights alone at the screen\nCode must be completed')
intros.append('Cursor is blinking\nThe prompt awaits your command\nTry entering "help"')

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
        raise utils.GambeziInvalidObject('[!] Error trying to build full type for: ' + str(otype))
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

def configure_base_object(obj):
    done = False
    try:
        while False == done:
            default = ''
            if obj.name in obj.defaults:
                default = obj.defaults[obj.name]
            if const.TAG_VALUE in obj.value.keys():
                default = obj.value[const.TAG_VALUE]
            print('Enter value for ' + obj.name + ' (' + str(default) + '): ')
            x = input()
            # If they just hit enter, keep and print the current value
            if len(x) == 0:
                x = default
                print(str(default))
            obj.value[const.TAG_VALUE] = x
            done = True
    except Exception as e:
        s = 'Value entry error (' + obj.name + '): ' + str(e) + '\n'
        s += obj.name + ' has type: ' + str(obj.type) + '\n'
        if hasattr(obj,'desc') and None is not obj.desc:
            s += obj.name + ' description: ' + obj.desc + '\n'
        raise utils.GambeziConfigureError(s)

def configure_member(obj,mtype,key):
    done = False
    try:
        while False == done:
            default = ''
            if key in obj.defaults:
                default = obj.defaults[key]
            if (key in obj.value):
                default = obj.value[key]
            print('Enter value for ' + mtype.name + ' (' + str(default) + '): ')
            x = input()
            # If they just hit enter, keep and print the current value
            if len(x) == 0:
                x = default
                print(str(default))
            obj.value[key] = x
            done = True
    except Exception as e:
        s = 'Value entry error (' + mtype.name + '): ' + str(e) + '\n'
        s += mtype.name + ' has type: ' + str(mtype.type) + '\n'
        if None is not mtype.desc:
            s += mtype.name + ' description: ' + mtype.desc + '\n'
        raise utils.GambeziConfigureError(s)

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
            # Copy the unknown defaults to each object because we don't know which
            # ones different members will require...
            for defkey in obj.defaults.keys():
                if False == (defkey in new_object.defaults.keys()):
                    new_object.defaults[defkey] = obj.defaults[defkey]
            stype = ui.find_type(mtype.type)
            configure_struct(ui,new_object,stype)
            obj.value[key] = new_object 

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

    # We don't want to repeat a command if the user just hits enter...
    def precmd(self,line):
        if (line is None) or (0 == len(line)):
            return 'help'
        return line

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
            print('[do_show] atypes: ' + str(atypes))
            for atype in atypes:
                print(atype.name)
        elif arg == 'values':
            print('Configured values:')
            for key in self.obj.value.keys():
                if const.TAG_ITEMTYPE == key:
                    continue
                v = self.obj.value[key]
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
            if arg == atype.name:
                if isinstance(atype,ui_config.UiStruct):
                    name_ok = False
                    while False == name_ok:
                        name_found = False
                        mid = input('Please enter an ID for ' + arg + ': ')
                        full_name = arg + const.ID_SEP + mid
                        for key in self.obj.value.keys():
                            if full_name == key:
                                name_found = True
                                break
                        if name_found:
                            print('\t[*] ID "' + mid + '" is in use, IDs must be unique')
                        else:
                            name_ok = True
                    obj = ui_config.create_object_from_type(atype,utils.get_namespace(atype.name))
                    configure_struct(self.ui,obj,atype)
                    self.obj.value[full_name] = obj
                    found = True
                else:
                    print('Trying to add invalid type (' + str(type(atype)) + ') to the application')
        if False == found:
            print('Unknown type: ' + arg)
            print('The following types are available:')
            for x in atypes:
                print(x.name)
        return False

    def complete_add(self,text,line,begidx,endidx):
        rv = list()
        atypes = self.get_available_types()
        if 0 == begidx and 0 == endidx:
            for atype in atypes:
                rv.append(atype.name)
        else:
            for atype in atypes:
                if atype.name.startswith(line[begidx:endidx]):
                    parts = atype.name.split(const.TYPE_SEP)
                    if len(parts) == 2:
                        rv.append(parts[0])
        return rv

    def do_remove(self,arg):
        'Remove a component from the list: i.e. remove <id>'
        fullname = None
        if 0 == len(arg):
            print('Please specify the id of the component to remove (one of the following):')
            for key in self.obj.value.keys():
                if const.ID_SEP in key:
                    parts = key.split(const.ID_SEP)
                    if len(parts) == 2:
                        print('\t' + parts[1])
        else:
            x = None
            for key in self.obj.value.keys():
                if const.ID_SEP in key:
                    parts = key.split(const.ID_SEP)
                    if len(parts) == 2:
                        if parts[1] == arg:
                            x = self.obj.value[key]
                            fullname = key
                            break
            if None is not x:
                x = input('Remove component with ID: ' + str(arg) + '? (y/n) ')
                if x in const.AFFIRMATIVE:
                    if None is not fullname:
                        self.obj.value.pop(fullname)
            else:
                print("Couldn't find component with ID: " + '"' + str(arg) + '"')
        return False

    def complete_remove(self,text,line,begidx,endidx):
        rv = list()
        atypes = self.get_available_types()
        if 0 == begidx and 0 == endidx:
            for key in self.obj.value.keys():
                if const.ID_SEP in key:
                    parts = key.split(const.ID_SEP)
                    if len(parts) == 2:
                        rv.append(parts[1])
        else:
            for key in self.obj.value.keys():
                if const.ID_SEP in key:
                    parts = key.split(const.ID_SEP)
                    if len(parts) == 2:
                        if parts[1].startswith(line[begidx:endidx]):
                            rv.append(parts[1])
        return rv

    def do_save(self,arg):
        'Save the current list and return to app configuration.'
        print('Saving list and returning to app configuration')
        self.app.ui = self.ui
        return True

    def get_available_types(self):
        atypes = list()
        if const.TAG_ITEMTYPE in self.obj.value.keys():
            itemtype = self.obj.value[const.TAG_ITEMTYPE]
            otype = self.ui.find_type(itemtype)
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

    def setup(self,parent,name,download_status):
        self.meta = parent.meta
        self.ui = parent.ui.clone()
        self.parent = parent
        self.name = name
        self.prompt = name + '> '
        app = None
        for x in self.meta.apps:
            if x.name == name:
                app = x
        if (None is not app) and (download_status == const.DOWNLOAD_COMPLETED):
            self.download_subs(app)
        if None is not app:
            self.download_app_modules(app,download_status)
        self.fixup_deployment(app)

    # We don't want to repeat a command if the user just hits enter...
    def precmd(self,line):
        if (line is None) or (0 == len(line)):
            return 'help'
        return line

    def fixup_deployment(self,app):
        deploy_dir = os.path.join(app.download_path,const.DEPLOY_DIR)
        for f in os.listdir(deploy_dir):
            if f.endswith(const.SHELL_SUFFIX):
                path = os.path.join(deploy_dir,f)
                os.chmod(path,stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)

    def download_app_modules(self,app,download_status):
        dst = os.path.expanduser(os.path.join(self.meta.staging,app.name))
        for x in self.meta.modules:
            if x.loader == app.name:
                if const.DOWNLOAD_COMPLETED:
                    utils.download_component(self.meta.staging,x)
                parse_ui(self.meta,self.ui,x)

    def download_subs(self,app):
        dst = os.path.expanduser(os.path.join(self.meta.staging,app.name))
        for sub in app.subs:
            downloaded = utils.download_file(sub.url,dst,True)
            basename = os.path.basename(downloaded)
            if basename.endswith(const.ZIP_SUFFIX):
                basename = basename[0:-len(const.ZIP_SUFFIX)]
            if basename.endswith(const.GITHUB_MAIN_SUFFIX):
                basename = basename[0:-len(const.GITHUB_MAIN_SUFFIX)]
            if None is not downloaded:
                for f in os.listdir(downloaded):
                    if f != '.' and f != '..':
                        src_path = os.path.join(downloaded,f)
                        dst_path = app.download_path
                        if None is not sub.dst:
                            dst_path = os.path.join(dst_path,sub.dst)
                        dst_path = os.path.join(dst_path,basename)
                        dst_path = os.path.join(dst_path,f)
                        shutil.copy(src_path,dst_path)

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
                print("[!] Couldn't find UI configuration for " + self.name)
        else:
            found = False
            for key in self.ui.components[self.name]:
                if key == arg:
                    obj = self.ui.components[self.name][key]
                    if obj.type in const.BASE_TYPES:
                        configure_base_object(obj)
                    else:
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
        for obj_key in self.ui.components[self.name].keys():
            obj = self.ui.components[self.name][obj_key]

            if 0 == len(obj.value):
                if obj.type in const.BASE_TYPES:
                    # There should be only one value. If not, we'll get the last one...
                    for key in obj.defaults.keys():
                        obj.value[const.TAG_VALUE] = obj.defaults[key]
                else:
                    for def_key in obj.defaults.keys():
                        obj.value[def_key] = obj.defaults[def_key]

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

    # We don't want to repeat a command if the user just hits enter...
    def precmd(self,line):
        if (line is None) or (0 == len(line)):
            return 'help'
        return line

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
                    v = obj.value
                    if 0 == len(obj.value):
                        print("Can't build. Empty value found for " + str(obj.name))
                        rv = False
                    # if it has a 'itemtype' tag, treat it as a list
                    elif const.TAG_ITEMTYPE in v.keys():
                        # if the list doesn't have anything else in it 
                        if 1 == len(v.keys()):
                            print("Can't build. Empty list found for " + str(obj.name))
                            rv = False
        return rv

    def build_it(self):
        if None is not self.meta.apps:
            for app in self.meta.apps:
                if app.configured:
                    base_path = os.path.join(app.download_path,const.DEPLOYMENT_DIR)
                    settings_path = os.path.join(base_path,const.SETTINGS_FILE_NAME)
                    self.write_app_settings(app,settings_path)
                    prefix = app.name
                    version = str(const.VERSION)
                    commit = utils.get_commit(app.meta_url)
                    self.build_bundle(app,base_path,prefix,version,commit)

    def do_build(self,arg):
        'Build one or more installer scripts. This command should be run after the "configure" command'
        if True == self.check_build():
            self.build_it()
        return False 

    def do_reset(self,arg):
        'Reset the configuration context (clear cache etc.). This command will delete current configurations'
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
        'Configure an application for installation: i.e. configure logger. Afterwards, run the "build" command to create the installer script'
        found = False
        for app in self.meta.apps:
            if app.name == arg:
                found = True
                status = utils.download_component(self.meta.staging,app)
                if status == const.DOWNLOAD_SKIPPED:
                    print('\tIf desired, use the "reset" command to delete cache and force download')
                if status > const.DOWNLOAD_FAILED:
                    parse_ui(self.meta,self.ui,app)
                    self.configure_app(app,status)
                else:
                    print('[!] Error downloading ' + str(app.name))
                break
        if False == found:
            print('Cannot configure unknown element: ' + str(arg))
            print('The following are elements that may be configured:')
            print('Apps')
            print('----')
            for app in self.meta.apps:
                print('\t' + str(app.name))
        return False

    def complete_configure(self,text,line,begidx,endidx):
        rv = list()
        if 0 == begidx and 0 == endidx:
            for app in self.meta.apps:
                rv.append(app.name)
        else:
            for app in self.meta.apps:
                if app.name.startswith(line[begidx:endidx]):
                    rv.append(app.name)
        return rv

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

    def do_quit(self,arg):
        'Quit the program. If the build command is not run before quitting, configurations will not be saved.'
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
            print('[!] Error parsing metadata: ' + str(e))

    def configure_app(self,app,download_status):
        app_config = CcsAppConfigurator()
        app_config.setup(self,app.name,download_status)
        app_config.cmdloop()

    def write_settings_member(self,obj,fd):
        print('[write_settings_member] THIS IS NOT IMPLEMENTED YET!')

    def write_settings_list(self,obj,fd):
        if None is not obj.value:
            if False == const.TAG_ITEMTYPE in obj.value.keys():
                # FIXME: throw an exception?
                return
            name = obj.name
            itemname = obj.value[const.TAG_ITEMTYPE]
            itemtype = self.ui.find_type(itemname)
            fd.write('<' + name + '>\n')
            for key in obj.value.keys():
                if key == const.TAG_ITEMTYPE:
                    continue
                itemobj = obj.value[key]
                if itemobj.type in const.BASE_TYPES:
                    self.write_settings_base_object(itemobj,fd)
                else:
                    if isinstance(itemtype,ui_config.UiMember):
                        self.write_settings_member(itemobj,fd)
                    elif isinstance(itemtype,ui_config.UiStruct):
                        self.write_settings_struct(itemobj,fd,itemtype.name)
                    elif isinstance(itemtype,ui_config.UiList):
                        self.write_settings_list(itemobj,fd)
                    else:
                        print('[write_settings_list] ??')
            fd.write('</' + name + '>\n')

    # The 'name' parameter needs a little explanation. It is currently only
    # used when calling write_settings_struct from write_settings_list. By
    # setting 'name' to the list's itemtype name, each object in the list
    # will get a surrounding tag with the itemtype name.
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
        for key in obj.value.keys():
            member = obj.value[key]
            if isinstance(member,ui_config.UiObject):
                self.write_settings_struct(member,fd)
            else:
                fd.write('<' + key + '>\n')
                fd.write(str(member) + '\n')
                fd.write('</' + key + '>\n')
        fd.write('</' + name + '>\n')

    def write_settings_base_object(self,obj,fd):
        fd.write('<' + obj.name + '>')
        fd.write(str(obj.value['value']))
        fd.write('</' + obj.name + '>\n')

    def write_app_settings(self,app,path):
        print('Writing settings.cfg for ' + str(app.name) + ' (' + path + ')')
        with open(path,'wt') as fd:
            fd.write(const.XML_PREFIX + '\n')
            fd.write('<' + TAG_CONFIG_ROOT + ' ' + ATTRIB_VERSION + CONFIG_VERSION + '>\n')
            for key in self.ui.components[app.name].keys():
                obj = self.ui.components[app.name][key]
                if obj.type in const.BASE_TYPES:
                    self.write_settings_base_object(obj,fd)
                else:
                    otype = self.ui.find_type(obj.type)
                    if isinstance(otype,ui_config.UiStruct):
                        self.write_settings_struct(obj,fd)
                    elif isinstance(otype,ui_config.UiList):
                        self.write_settings_list(obj,fd)
                    else:
                        print('[write_app_settings] ??')
            fd.write('</' + TAG_CONFIG_ROOT + '>\n')

    def build_bundle(self,app,base_path,prefix,version,commit):
        print('Building install bundle for ' + app.name)
        try:
            # Find the meta modules that have the app name as the loader
            # Copy them to the "<prefix>mod" directory
            print('Copying modules...')
            for mod in self.meta.modules:
                if app.name == mod.loader:
                    dst_dir = mod.prefix + const.MOD_SUFFIX
                    dst_path = os.path.join(app.download_path,dst_dir)
                    src_path = os.path.join(mod.download_path,mod.name + const.PYTHON_SUFFIX)
                    print(src_path + ' --> ' + dst_path)
                    shutil.copy(src_path,dst_path)

            # Change working directory
            cwd = os.getcwd()
            os.chdir(base_path)
            # Call the build script
            if os.path.exists(const.BUILD_SCRIPT_NAME):
                cmd = 'python ' + const.BUILD_SCRIPT_NAME + ' -p ' + str(prefix) + ' -v ' + str(version) +  ' -c ' + str(commit)
                subprocess.run(cmd.split(' '))
                script_src_path = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
                script_src_path = script_src_path.decode('utf-8')
                if (None is not script_src_path) and (len(script_src_path) > 0):
                    basename = os.path.basename(script_src_path)
                    script_dst_path = os.path.join(cwd,basename) 
                    shutil.copy(script_src_path,script_dst_path)
                    print('\n')
                else:
                    print('[!] Bundle builder failed to return a path')
            else:
                full_path = os.path.join(base_path,const.BUILD_SCRIPT_NAME)
                print("[!] Error: Couldn't find script " + full_path)
            os.chdir(cwd)
        except Exception as ex:
            print('[!] Error trying to build bundle: ' + str(ex))

    def get_loader_app(self,name):
        rv = None
        for app in self.meta.apps:
            if app.name == name:
                rv = app
                if False == app.cached:
                    status = utils.download_component(self.meta.staging,app)
                    if status == const.DOWNLOAD_FAILED:
                        print('[!] Error downloading ' + str(app.name))
        return rv

    def set_ui(self,ui):
        self.ui = ui

def print_intro():
    print('\n')
    print(intros[random.randint(0,len(intros)-1)])
    print('\n')


if '__main__' == __name__:
    print(banner)
    print_intro()
    try:
        build_installer = CcsBuildInstaller()
        build_installer.parse_metadata(DEFAULT_META_PATH)
        build_installer.parse_local_ui()
        # build_installer.do_help('')
        build_installer.cmdloop()
    except KeyboardInterrupt:
        print('\nbye...')
    except Exception as e:
        print(traceback.format_exc())
        print('Exception: ' + str(type(e)))
        print('[__main__] ' + str(e))
        traceback.print_stack()

