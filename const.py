"""
    const.py
    Constants for Gambezi

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

# Basic Types 
TYPE_BOOLEAN       = 'boolean'
TYPE_BYTE          = 'byte'
TYPE_CHAR          = 'char'
TYPE_INT           = 'int'
TYPE_FLOAT         = 'float'
TYPE_STRING        = 'string'

BASE_TYPES         = [TYPE_BOOLEAN,TYPE_BYTE,TYPE_CHAR,TYPE_INT,TYPE_FLOAT,TYPE_STRING]

# Complex Types 
TYPE_STRUCT        = 'struct'
TYPE_LIST          = 'list'

AFFIRMATIVE        = ['y','Y','yes','Yes','YES','t','true','True','TRUE']
WHITESPACE         = [' ','\t','\r','\n']

DOCS_DIR           = 'docs'
UI_FILE            = 'ui.xml'

TAG_ABSTRACT       = 'abstract'
TAG_CCS_UI         = 'ccs-ui'
TAG_DEFAULTS       = 'defaults'
TAG_DESC           = 'desc'
TAG_IGNORE         = 'ignore'
TAG_INHERITANCE    = 'inheritance'
TAG_LIST           = 'list'
TAG_MEMBER         = 'member'
TAG_NAME           = 'name'
TAG_NAMESPACE      = 'ns'
TAG_OBJECT         = 'object'
TAG_STRUCT         = 'struct'
TAG_ITEMTYPE       = 'itemtype'
TAG_SUPER          = 'super'
TAG_TYPE           = 'type'
TAG_TYPES          = 'types'
TAG_UI             = 'ui'
TAG_VALUE          = 'value'

XML_PREFIX         = '<?xml version="1.0" encoding="UTF-8"?>'
SETTINGS_FILE_NAME = 'settings.cfg'
UNSPECIFIED        = 'unspecified'

DOWNLOAD_UNKNOWN   = -2
DOWNLOAD_FAILED    = -1
DOWNLOAD_SKIPPED   = 0
DOWNLOAD_COMPLETED = 1

SHELL_SUFFIX       = '.sh'
PYTHON_SUFFIX      = '.py'
ZIP_SUFFIX         = '.zip'
GITHUB_MAIN_SUFFIX = '-main'
DEPLOY_DIR         = 'deployment'
MOD_SUFFIX         = 'mods'

ID_SEP             = '/'
TYPE_SEP           = ':'

BUILD_SCRIPT_NAME  = 'build_bundle.py'
VERSION            = 1
COMMIT_MARKER      = 'data-hovercard-type="commit"'
COMMIT_URL_MARKER  = 'data-hovercard-url'
