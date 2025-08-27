import sys
import os
import logging

# Suppress Qt's FFmpeg warnings
os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.ffmpeg.warning=false'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, # Set to DEBUG for detailed logs, INFO for less verbose
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to console
    ]
)



from PyQt6.QtWidgets import QApplication, QFileDialog
from dataset_quick_view.main_window import MainWindow
from dataset_quick_view.utils.config_manager import ConfigManager



logger = logging.getLogger(__name__)

def show_folder_dialog():
    """Opens a dialog to select a folder and returns the path."""
    dialog = QFileDialog()
    folder_path = dialog.getExistingDirectory(None, "Select Dataset Folder")
    return folder_path

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    config = ConfigManager()

    folder_path = ""
    # Check for command-line arguments first
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        logger.info(f"Loading folder from command-line argument: {folder_path}")
    else:
        # Otherwise, check the config for the last used folder
        if config.get_bool_setting('General', 'remember_last_folder'):
            last_path = config.get_setting('General', 'last_folder_path')
            if os.path.isdir(last_path):
                logger.info(f"Loading last used folder: {last_path}")
                folder_path = last_path

        # If no path is set yet, show the dialog
        if not folder_path:
            logger.info("No folder specified, showing dialog...")
            folder_path = show_folder_dialog()

    if not folder_path or not os.path.isdir(folder_path):
        logger.error("No valid folder selected. Exiting.")
        sys.exit(0)

    main_win = MainWindow(folder_path, config)
    main_win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
