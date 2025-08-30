class SettingsManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.config = main_window.config

    def load_settings(self):
        self.main_window.auto_save_checkbox.setChecked(self.config.get_bool_setting('Editing', 'auto_save'))
        self.main_window.remember_folder_checkbox.setChecked(self.config.get_bool_setting('General', 'remember_last_folder'))
        self.main_window.recursive_checkbox.setChecked(self.config.get_bool_setting('General', 'recursive_search'))

    def save_settings(self):
        self.config.set_setting('Editing', 'auto_save', str(self.main_window.auto_save_checkbox.isChecked()))
        self.config.set_setting('General', 'remember_last_folder', str(self.main_window.remember_folder_checkbox.isChecked()))
        self.config.set_setting('General', 'recursive_search', str(self.main_window.recursive_checkbox.isChecked()))
        self.config.set_setting('Display', 'font_size', str(self.main_window.app_state.current_font_size))
        if self.main_window.remember_folder_checkbox.isChecked():
            self.config.set_setting('General', 'last_folder_path', self.main_window.app_state.folder_path)
        self.config.save_config()
