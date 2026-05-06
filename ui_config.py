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

class InvalidUiConfigElement(Exception):
    pass

import xml.etree.ElementTree as et

TAG_CCS_UI         = 'ccs-ui'
TAG_DEFAULT        = 'default'
TAG_DESC           = 'desc'
TAG_INHERITANCE    = 'inheritance'
TAG_LIST           = 'list'
TAG_MEMBER         = 'member'
TAG_NAME           = 'name'
TAG_NAMESPACE      = 'ns'
TAG_OBJECT         = 'object'
TAG_STRUCT         = 'struct'
TAG_SUBTYPE        = 'subtype'
TAG_SUPER          = 'super'
TAG_TYPE           = 'type'
TAG_TYPES          = 'types'
TAG_UI             = 'ui'

# Basic Types 
TYPE_BYTE          = 'byte'
TYPE_CHAR          = 'char'
TYPE_INT           = 'int'
TYPE_FLOAT         = 'float'
TYPE_STRING        = 'string'

BASE_TYPES         = [TYPE_BYTE,TYPE_CHAR,TYPE_INT,TYPE_FLOAT,TYPE_STRING]

# Complex Types 
TYPE_STRUCT        = 'struct'
TYPE_LIST          = 'list'

class InvalidCcsUiFile(Exception):
    pass

class UiMember(object):

    def __init__(self):
        self.name = None
        self.type = None
        self.desc = None
        self.default = None

    def clone(self):
        rv = UiMember()
        rv.name = self.name
        rv.type = self.type
        rv.desc = self.desc
        rv.default = self.default
        return rv

    def __repr__(self):
        s = 'Member:\n'
        if hasattr(self,'name') and None is not self.name:
            s += '\tname: ' + str(self.name) + '\n'
        if hasattr(self,'type') and None is not self.type:
            s += '\ttype: ' + str(self.type) + '\n'
        if hasattr(self,'desc') and None is not self.desc:
            s += '\tdesc: ' + str(self.desc) + '\n'
        if hasattr(self,'default') and None is not self.default:
            s += '\tdefault: ' + str(self.default) + '\n'
        return s

class UiType(object):

    def __init__(self):
        self.name = None
        self.desc = None

    def __repr__(self):
        s = ''
        if hasattr(self,'name') and None is not self.name:
            s += '\tname: ' + str(self.name) + '\n'
        if hasattr(self,'type') and None is not self.type:
            s += '\ttype: ' + str(self.type) + '\n'
        if hasattr(self,'desc') and None is not self.desc:
            s += '\tdesc: ' + str(self.desc) + '\n'
        return s

class UiStruct(UiType):

    def __init__(self):
        super().__init__()
        self.members = dict()
        self.type = TYPE_STRUCT 
        self.super_types = list()

    def clone(self):
        rv = UiStruct()
        rv.name = self.name
        rv.desc = self.desc
        for key in self.members.keys():
            rv.members[key] = self.members[key].clone()
        for st in self.super_types:
            rv.super_types.append(st)
        return rv

    def __repr__(self):
        s = super().__repr__()
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
        self.subtype = None 
        self.type = TYPE_LIST 

    def clone(self):
        rv = UiList()
        rv.name = self.name
        rv.desc = self.desc
        rv.subtype = self.subtype
        return rv

    def __repr__(self):
        s = super().__repr__()
        if hasattr(self,'subtype') and None is not self.subtype:
            s += '\tsubtype: ' + str(self.subtype) + '\n'
        return s

class UiObject(object):
    def __init__(self):
        self.type = None
        # For basic types, the first value in the values dictionary
        # contains the value of the object. The key is 'value'

        # For a struct, the dictionary contains the values of the 
        # members

        # For a list, the first value in the values dictionary
        # contains the list subtype. The key is 'subtype', the value
        # is the name of the type. 
        # The second value in the dictionary contains a list with the 
        # specific type (could be a subtype of the 'subtype') and name 
        # of each object in the list. For this list, the type name and
        # identifier are separated by a forward slash: '/'. The key is 
        # 'objects'.
        # Subsequent values in the list have the type name and identifier
        # string as listed in the second value as the key, with the value
        # being a UiObject containing the actual data for the named object.
        self.values = dict()

    def clone(self):
        rv = UiObject()
        rv.type = self.type
        for key in self.values.keys():
            rv.values[key] = self.values[key]
        return rv

    def __repr__(self):
        s = 'Object:\n'
        if None is not self.type:
            s += '\ttype: ' + str(self.type) + '\n'
            s += '\tvalues: ' + str(self.values) + '\n'
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
        print('Parsing types from: ' + path)
        tree = et.parse(path)
        root = tree.getroot()
        if root.tag == TAG_CCS_UI:
            types_node = root.find(TAG_TYPES)
            if None is not types_node:
                struct_nodes = types_node.findall(TAG_STRUCT)
                for struct_node in struct_nodes:
                    self.parse_struct_node(struct_node)
                list_nodes = types_node.findall(TAG_LIST)
                for list_node in list_nodes:
                    self.parse_list_node(list_node)
            else:
                raise InvalidCcsUiFile('Types element not found')
        else:
            raise InvalidCcsUiFile('Not a valid CCS UI file')

    def parse_ui(self,path,name):
        print('Parsing ui from: ' + path)
        tree = et.parse(path)
        root = tree.getroot()
        if root.tag == TAG_CCS_UI:
            ui_node = root.find(TAG_UI)
            self.components[name] = dict()
            if None is not ui_node:
                object_nodes = ui_node.findall(TAG_OBJECT)
                for object_node in object_nodes:
                    obj = self.parse_object_node(object_node,name)
                    t = self.find_type(obj.type)
                    if None is not t:
                        if TYPE_LIST == t.type:
                            obj.values['subtype'] = t.subtype
                    self.components[name][obj.name] = obj
            else:
                raise InvalidCcsUiFile('ui element not found')
        else:
            raise InvalidCcsUiFile('Not a valid CCS UI file')

    def parse_struct_node(self,node):
        new_struct = UiStruct()
        ns = None
        ns_node = node.find(TAG_NAMESPACE)
        if None is not ns_node:
            ns = ns_node.text.strip()
        name_node = node.find(TAG_NAME)
        name = None
        if None is not name_node:
            name = name_node.text.strip()
        if name is None:
            raise InvalidUiConfigElement('struct element has no name')
        if None is ns:
            new_struct.name = name
        else:
            new_struct.name = ns + ':' + name
        desc_node = node.find(TAG_DESC)
        if None is not desc_node:
            new_struct.desc = desc_node.text.strip()
        member_nodes = node.findall(TAG_MEMBER)
        for member_node in member_nodes:
            self.parse_member_node(new_struct,member_node)
        inheritance_node = node.find(TAG_INHERITANCE)
        if None is not inheritance_node:
            super_types = inheritance_node.findall(TAG_SUPER)
            if None is not super_types:
                for nd in super_types:
                    print('[parse_struct_node] appending super type: ' + str(nd.text.strip()))
                    new_struct.super_types.append(nd.text.strip())
        # FIXME: Do error checking, including name collisions
        self.types[new_struct.name] = new_struct

        #print('[parse_struct_node] new_struct: ' + str(new_struct))

    def parse_member_node(self,struct,node):
        new_member = UiMember()
        name_node = node.find(TAG_NAME)
        if None is not name_node:
            new_member.name = name_node.text.strip()
        else:
            raise InvalidUiConfigElement('member element has no name')
        desc_node = node.find(TAG_DESC)
        if None is not desc_node:
            new_member.desc = desc_node.text.strip()
        type_node = node.find(TAG_TYPE)
        if None is not type_node:
            new_member.type = type_node.text.strip()
        else:
            raise InvalidUiConfigElement('member element has no type')
        def_node = node.find(TAG_DEFAULT)
        if None is not def_node:
            new_member.default = def_node.text.strip()
        struct.members[new_member.name] = new_member

    def clone(self):
        rv = UiConfig()
        for key in self.types.keys():
            rv.types[key] = self.types[key].clone()
        for comp_name in self.components.keys():
            comp = self.components[comp_name]
            for obj_name in comp[comp_name].keys():
                rv.components[comp_name][obj_name] = dict()
                obj = self.components[comp_name][obj_name].clone() 
                rv.components[comp_name][obj_name] = obj
        return rv

    def parse_list_node(self,node):
        new_list = UiList()
        ns = None
        ns_node = node.find(TAG_NAMESPACE)
        if None is not ns_node:
            ns = ns_node.text.strip()
        name = None
        name_node = node.find(TAG_NAME)
        if None is not name_node:
            name = name_node.text.strip()
        if name is None:
            raise InvalidUiConfigElement('list element has no name')
        if None is ns:
            new_list.name = name
        else:
            new_list.name = ns + ':' + name
        desc_node = node.find(TAG_DESC)
        if None is not desc_node:
            new_list.desc = desc_node.text.strip()
        subtype_node = node.find(TAG_SUBTYPE)
        if None is not subtype_node:
            new_list.subtype = subtype_node.text.strip()
        # FIXME: Do error checking, including name collisions
        self.types[new_list.name] = new_list

    def parse_object_node(self,node,name):
        new_object = UiObject()
        type_node = node.find(TAG_TYPE)
        if None is not type_node:
            new_object.type = type_node.text.strip()
        else:
            raise InvalidUiConfigElement('object element has no type')
        name_node = node.find(TAG_NAME)
        if None is not name_node:
            new_object.name = name_node.text.strip()
        else:
            raise InvalidUiConfigElement('object element has no name')
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

    def get_name(self,fullname):
        rv = ''
        if fullname.startswith(':'):
            rv = fullname[1:] 
        elif ':' in fullname:
            parts = fullname.split(':')
            rv = parts[1]
        else:
            rv = fullname
        return rv

    def __repr__(self):
        s = 'Config:\n'
        if None is not self.types:
            s += '***** Types *****\n'
            for v in self.types:
                s += str(self.types[v]) 
            s += '\n'
        if None is not self.components:
            for c in self.components:
                s += c + '\n'
                for o in self.components[c]:
                    s += str(self.components[c][o]) 
            s += '\n'
        return s


