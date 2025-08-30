class AppState:
    def __init__(self, folder_path, config):
        self.folder_path = folder_path
        self.config = config
        self.dataset = {}
        self.text_cache = {}
        self.dirty_files = set()
        self.detached_viewer = None
        self.current_font_size = int(self.config.get_setting('Display', 'font_size'))
