# DatasetQuickView

DatasetQuickView is a utility for quickly viewing and editing image and text datasets. It's designed to streamline the process of reviewing and cleaning up datasets for AI and machine learning projects.

## Features

*   **Dual Panel View:** Simultaneously view a list of files and the content of the selected file.
*   **File Browser:** Navigate your dataset with a recursive file list that supports filtering by extension.
*   **Text Editor:** View and edit text files directly within the application with auto-save functionality.
*   **Media Viewer:** Supports a wide range of image formats (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.gif`) and video files (`.mp4`).
*   **Editing Tools:**
    *   **Find and Replace:** Quickly find and replace text in the open text file.
    *   **Prefix & Suffix:** Add prefixes and suffixes to filenames.
*   **Customizable Layout:** Adjust panel sizes and font size to your liking. All settings are saved in `config.ini`.

## Requirements

*   Python 3.12
*   PyQt6
*   Pillow

## Setup

1.  **Create Virtual Environment:** Run the `venv_create.bat` script to automatically create a Python virtual environment. It will also offer to install the required packages.
2.  **Install Dependencies:** If you didn't install the packages in the previous step, activate the environment (`venv_activate.bat`) and run:
    ```bash
    pip install -r requirements.txt
    ```

## How to Use

1.  **Activate Environment:** Run `venv_activate.bat`.
2.  **Run Application:** Execute the main application script:
    ```bash
    python app.py
    ```
3.  **Open Folder:** Use the "Open Folder" button to select the root directory of your dataset.
4.  **Navigate and Edit:** Click on files in the list to view them. Text files can be edited in the text panel. Use the "Tools" menu for advanced editing options.


