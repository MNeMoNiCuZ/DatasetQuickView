import configparser
import os
import sys
import logging

logger = logging.getLogger(__name__)

def get_app_base_path():
    """Get the base path for the application, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        return os.path.dirname(sys.executable)
    else:
        # Running from source, place it in the project root
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join(get_app_base_path(), 'config.ini')
        self.config = configparser.ConfigParser()
        self.defaults = {
            'General': {
                'config_version': '1',
                'remember_last_folder': 'false',
                'last_folder_path': ''
            },
            'Editing': {
                'auto_save': 'true'
            },
            'Display': {
                'font_size': '10'
            },
            'MediaFormats': {
                'supported': '.png,.jpg,.jpeg,.bmp,.webp,.gif,.mp4',
                'png': 'true',
                'jpg': 'true',
                'jpeg': 'true',
                'bmp': 'true',
                'webp': 'true',
                'gif': 'true',
                'mp4': 'true'
            },
            'Video': {
                'loop': 'true'
            },
            'Program': {
                'file_list_width': '250',
                'text_editor_width': '300'
            }
        }
        self.load_or_create_config()

    def load_or_create_config(self):
        if not os.path.exists(self.config_path):
            self.config.read_dict(self.defaults)
            self.save_config()
        else:
            self.config.read(self.config_path)
            self.check_and_update_config()

    def check_and_update_config(self):
        updated = False
        
        # Config versioning and migration
        config_version = int(self.get_setting('General', 'config_version', fallback='1'))

        # --- Migration Examples ---
        # if config_version < 2:
        #     # Migrate to version 2
        #     if not self.config.has_section('NewSection'):
        #         self.config.add_section('NewSection')
        #     self.set_setting('NewSection', 'new_key', 'default_value')
        #     self.set_setting('General', 'config_version', '2')
        #     config_version = 2 # Update local variable for sequential migrations
        #     updated = True

        # if config_version < 3:
        #     # Migrate to version 3
        #     # ...
        #     self.set_setting('General', 'config_version', '3')
        #     config_version = 3
        #     updated = True

        # Check for and add missing sections or keys from defaults
        for section, keys in self.defaults.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                updated = True
            for key, value in keys.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
                    updated = True
        if updated:
            self.save_config()

    def save_config(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def get_setting(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback or self.defaults.get(section, {}).get(key, None))

    def get_bool_setting(self, section, key, fallback=False):
        value = self.config.getboolean(section, key, fallback=fallback)
        return value

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))