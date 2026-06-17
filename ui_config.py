"""
    uiconfig.py  
    User-interface configuration 

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

import xml.etree.ElementTree as et

import const
import utils


def create_object_from_type(otype,name):
    rv = UiObject() 
    rv.type = otype.name
    rv.name = name
    for key in otype.defaults.keys():
        rv.defaults[key] = otype.defaults[key]
    return rv

class UiMember(object):

    def __init__(self):
        self.name = None
        self.type = None
        self.desc = None
        self.ignore = False

    def clone(self):
        rv = UiMember()
        rv.name = self.name
        rv.type = self.type
        rv.desc = self.desc
        rv.ignore = self.ignore
        return rv

    def __repr__(self):
        s = ''
        if hasattr(self,'name') and None is not self.name:
            s += '\tname: ' + str(self.name) + '\n'
        if hasattr(self,'type') and None is not self.type:
            s += '\ttype: ' + str(self.type) + '\n'
        if hasattr(self,'desc') and None is not self.desc:
            s += '\tdesc: ' + str(self.desc) + '\n'
        if hasattr(self,'ignore') and None is not self.desc:
            s += '\tignore: ' + str(self.ignore) + '\n'
        return s

class UiType(object):

    def __init__(self):
        self.name = None
        self.desc = None

    def __repr__(self):
        s = '=================\n'
        if hasattr(self,'name') and None is not self.name:
            s += '\tname: ' + str(self.name) + '\n'
        if hasattr(self,'desc') and None is not self.desc:
            s += '\tdesc: ' + str(self.desc) + '\n'
        return s

class UiStruct(UiType):

    def __init__(self):
        super().__init__()
        self.members = dict()
        self.type = const.TYPE_STRUCT 
        self.super_types = list()
        self.abstract = False
        # For a struct type, the defaults dictionary contains values
        # for each of the members in the struct. The key is the
        # member name, the value is the member value 
        self.defaults = dict()


    def clone(self):
        rv = UiStruct()
        rv.name = self.name
        rv.abstract = self.abstract
        rv.desc = self.desc
        for key in self.members.keys():
            rv.members[key] = self.members[key].clone()
        for st in self.super_types:
            rv.super_types.append(st)
        for key in self.defaults.keys():
            rv.defaults[key] = self.defaults[key]
        return rv

    def __repr__(self):
        s = super().__repr__()
        if hasattr(self,'abstract') and None is not self.abstract:
            s += '\tabstract: ' + str(self.abstract) + '\n'
        if None is not self.members:
            s += '\tmembers:\n'
            for key in self.members.keys():
                s += '\t\t' + str(self.members[key]) + '\n'
            s += '\tsuper types:\n'
            if (None is not self.super_types) and (len(self.super_types) > 0):
                for name in self.super_types:
                    s += '\t\t' + str(name) + '\n'
        return s

class UiList(UiType):
       
    def __init__(self):
        super().__init__()
        self.itemtype = None 
        self.type = const.TYPE_LIST 

    def clone(self):
        rv = UiList()
        rv.name = self.name
        rv.desc = self.desc
        rv.itemtype = self.itemtype
        return rv

    def __repr__(self):
        s = super().__repr__()
        if hasattr(self,const.TAG_ITEMTYPE) and None is not self.itemtype:
            s += '\titemtype: ' + str(self.itemtype) + '\n'
        return s

class UiObject(object):
    def __init__(self):
        self.type = None
        self.name = None
        # For basic types, the first value in the value dictionary
        # contains the value of the object. The key is 'value'

        # For a struct, the value dictionary contains the values of the 
        # members, using the name in the type and the associated value in the value

        # For a list, the value dictionary contains an item with the
        # key 'itemtype' and the value being the name of the type.  
        # Note that objects in the list may be subtypes of the 'itemtype'.
        # Subsequent values in the list have a type name and identifier
        # string separated by a forward slash ('/') as the key, with the value
        # being a UiObject containing the actual data for the named object.
        self.value = dict()

        # For basic types, the defaults dictionary
        # contains the value of the object. The key is 'value'

        # For a struct, the defaults dictionary contains values
        # for each of the members in the struct. The key is the
        # member name, the value is the member value 

        # For a list, the defaults dictionary contains the defaults
        # for each type in the list. The key is the type name (bme280:sensor),
        # The value is a dictionary as per the struct above.

        self.defaults = dict()

    def clone(self):
        rv = UiObject()
        rv.type = self.type
        rv.name = self.name
        for key in self.value.keys():
            rv.value[key] = self.value[key]
        for key in self.defaults.keys():
            rv.defaults[key] = self.defaults[key]
        return rv

    def __repr__(self):
        s = ''
        if None is not self.type:
            s += '\ttype: ' + str(self.type) + '\n'
        else:
            s += '\ttype: unknown' + '\n'
        if None is not self.name:
            s += '\tname: ' + str(self.name) + '\n'
        else:
            s += '\tname: unknown' + '\n'
        if None is not self.value:
            s += '\tvalue:\n'
            for key in self.value.keys():
                s += '\t\t' + str(key) + ': ' + str(self.value[key]) + '\n'
        else:
            s += '\tvalue: unknown' + '\n'
        #if None is not self.defaults:
        #    s += '\tdefaults:\n'
        #    for key in self.defaults.keys():
        #        s += '\t\t' + str(key) + ': ' + str(self.defaults[key]) + '\n'
        #else:
        #    s += '\tdefaults: unknown' + '\n'
        return s

class UiConfig(object):

    def __init__(self):
        # key is type name
        # value is a UiType object
        self.types = dict()
        # key is metabase name
        # value is a dictionary of {object name,UiObject}
        self.components = dict()

    def parse_types(self,path):
        tree = et.parse(path)
        root = tree.getroot()
        if root.tag == const.TAG_CCS_UI:
            types_node = root.find(const.TAG_TYPES)
            if None is not types_node:
                struct_nodes = types_node.findall(const.TAG_STRUCT)
                for struct_node in struct_nodes:
                    self.parse_struct_node(struct_node)
                list_nodes = types_node.findall(const.TAG_LIST)
                for list_node in list_nodes:
                    self.parse_list_node(list_node)
            else:
                raise utils.InvalidCcsUiFile('Types element not found')
        else:
            raise utils.InvalidCcsUiFile('Not a valid CCS UI file')

    def parse_ui(self,path,name):
        tree = et.parse(path)
        root = tree.getroot()
        if root.tag == const.TAG_CCS_UI:
            ui_node = root.find(const.TAG_UI)
            self.components[name] = dict()
            if None is not ui_node:
                object_nodes = ui_node.findall(const.TAG_OBJECT)
                for object_node in object_nodes:
                    obj = self.parse_object_node(object_node,name)
                    t = self.find_type(obj.type)
                    if None is not t:
                        if const.TYPE_LIST == t.type:
                            obj.value[const.TAG_ITEMTYPE] = t.itemtype
                    self.components[name][obj.name] = obj
            else:
                raise utils.InvalidCcsUiFile('ui element not found')
        else:
            raise utils.InvalidCcsUiFile('Not a valid CCS UI file')

    def parse_struct_node(self,node):
        new_struct = UiStruct()
        ns = None

        if const.TAG_ABSTRACT in node.attrib.keys():
            if node.attrib[const.TAG_ABSTRACT] in const.AFFIRMATIVE:
                new_struct.abstract = True
        ns_node = node.find(const.TAG_NAMESPACE)
        if None is not ns_node:
            ns = ns_node.text.strip()
        name_node = node.find(const.TAG_NAME)
        name = None
        if None is not name_node:
            name = name_node.text.strip()
        if name is None:
            raise utils.InvalidUiConfigElement('struct element has no name')
        if None is ns:
            new_struct.name = name
        else:
            new_struct.name = ns + ':' + name
        desc_node = node.find(const.TAG_DESC)
        if None is not desc_node:
            new_struct.desc = desc_node.text.strip()
        member_nodes = node.findall(const.TAG_MEMBER)
        for member_node in member_nodes:
            self.parse_member_node(new_struct,member_node)
        inheritance_node = node.find(const.TAG_INHERITANCE)
        if None is not inheritance_node:
            super_types = inheritance_node.findall(const.TAG_SUPER)
            if None is not super_types:
                for nd in super_types:
                    new_struct.super_types.append(nd.text.strip())
        defaults_node = node.find(const.TAG_DEFAULTS)
        if None is not defaults_node:
            for def_node in defaults_node:
                key = def_node.tag
                new_struct.defaults[key] = def_node.text.strip()
        # FIXME: Do error checking, including name collisions
        self.types[new_struct.name] = new_struct

    def parse_member_node(self,struct,node):
        new_member = UiMember()
        if const.TAG_IGNORE in node.attrib.keys():
            if node.attrib[const.TAG_IGNORE] in const.AFFIRMATIVE:
                new_member.ignore = True
        name_node = node.find(const.TAG_NAME)
        if None is not name_node:
            new_member.name = name_node.text.strip()
        else:
            raise utils.InvalidUiConfigElement('member element has no name')
        desc_node = node.find(const.TAG_DESC)
        if None is not desc_node:
            new_member.desc = desc_node.text.strip()
        type_node = node.find(const.TAG_TYPE)
        if None is not type_node:
            new_member.type = type_node.text.strip()
        else:
            raise utils.InvalidUiConfigElement('member element has no type')
        struct.members[new_member.name] = new_member

    def clone(self):
        rv = UiConfig()
        for key in self.types.keys():
            rv.types[key] = self.types[key].clone()
        for comp_name in self.components.keys():
            rv.components[comp_name] = dict()
            comp = self.components[comp_name]
            for obj_name in comp.keys():
                rv.components[comp_name][obj_name] = dict()
                obj = self.components[comp_name][obj_name].clone() 
                rv.components[comp_name][obj_name] = obj
        return rv

    def parse_list_node(self,node):
        new_list = UiList()
        ns = None
        ns_node = node.find(const.TAG_NAMESPACE)
        if None is not ns_node:
            ns = ns_node.text.strip()
        name = None
        name_node = node.find(const.TAG_NAME)
        if None is not name_node:
            name = name_node.text.strip()
        if name is None:
            raise utils.InvalidUiConfigElement('list element has no name')
        if None is ns:
            new_list.name = name
        else:
            new_list.name = ns + ':' + name
        desc_node = node.find(const.TAG_DESC)
        if None is not desc_node:
            new_list.desc = desc_node.text.strip()
        itemtype_node = node.find(const.TAG_ITEMTYPE)
        if None is not itemtype_node:
            new_list.itemtype = itemtype_node.text.strip()
        # FIXME: Do error checking, including name collisions
        self.types[new_list.name] = new_list

    def parse_object_node(self,node,name):
        new_object = UiObject()
        type_node = node.find(const.TAG_TYPE)
        if None is not type_node:
            new_object.type = type_node.text.strip()
        else:
            raise utils.InvalidUiConfigElement('object element has no type')
        name_node = node.find(const.TAG_NAME)
        if None is not name_node:
            new_object.name = name_node.text.strip()
        else:
            raise utils.InvalidUiConfigElement('object element has no name')
        defaults_node = node.find(const.TAG_DEFAULTS)
        if None is not defaults_node:
            for def_node in defaults_node:
                key = def_node.tag
                new_object.defaults[key] = def_node.text.strip()
        return new_object

    def find_type(self,name):
        rv = None
        for key in self.types.keys():
            if key == name:
                rv = self.types[key]
                break
        return rv

    # Find super_types of the struct with the given name
    def find_super_types(self,name):
        rv = list()
        for key in self.types.keys():
            if key == name:
                target = self.types[key]
                for nd in target.super_types:
                    rv.append(nd)
                break
        return rv

    # Find sub_types of the struct with the given name
    def find_sub_types(self,name):
        rv = list()
        for key in self.types.keys():
            otype = self.types[key]
            if isinstance(otype,UiStruct):
                for nd in otype.super_types:
                    if name == nd:
                        rv.append(otype.name)
        return rv

    def find_object_by_name(self,comp_name,obj_name):
        rv = None
        if None is not self.components:
            for comp_key in self.components.keys():
                if comp_name == comp_key:
                    for obj_key in self.components[comp_key].keys():
                        if obj_key == obj_name:
                            rv = self.components[comp_key][obj_key]
                            break
        return rv

    def __repr__(self):
        s = ''
        if None is not self.types:
            s += '***** Types *****\n'
            for v in self.types:
                s += str(self.types[v]) 
            s += '\n'
        if None is not self.components:
            s += '***** Components *****\n'
            for c in self.components:
                s += c + '\n'
                for o in self.components[c]:
                    s += str(self.components[c][o]) 
            s += '\n'
        return s


