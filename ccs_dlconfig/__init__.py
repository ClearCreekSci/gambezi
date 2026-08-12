'''
    __init__.py
    Package declaration and helper functions for CCS DataLogger configs

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



TRUE_LIST = ['TRUE','True','true','T','t','YES','Yes','yes','Y','y','1']

def interpret_boolean_value(s: str) -> bool:
    return s in TRUE_LIST

