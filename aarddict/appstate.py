"""
This file is part of AardDict (http://code.google.com/p/aarddict) - 
a dictionary for Nokia Internet Tablets. 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2006-2008 Igor Tkach
"""

from __future__ import with_statement
import os.path
import pickle

settings_dir  = ".aarddict"
app_state_file = "app_state"

def save_app_state(app_state):
    home_dir = os.path.expanduser('~')
    settings_dir_path = os.path.join(home_dir, settings_dir)
    if not os.path.exists(settings_dir_path): os.mkdir(settings_dir_path)
    settings = os.path.join(home_dir, settings_dir, app_state_file)
    with file(settings, "w") as settings_file:
        pickle.dump(app_state, settings_file)
    
def load_app_state():
    home_dir = os.path.expanduser('~')
    settings = os.path.join(home_dir, settings_dir, app_state_file)
    app_state = None
    if os.path.exists(settings):        
        with file(settings, "r") as settings_file:
            app_state = pickle.load(settings_file)
    return app_state
    
class State:  
    drag_selects = True
    phonetic_font = None
    word = None
    selected_word = None
    lang_positions = {}
    history = []
    recent = []
    dict_files = []
    last_dict_file_location = None    