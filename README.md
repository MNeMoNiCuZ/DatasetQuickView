# DatasetQuickView

DatasetQuickView is a utility for quickly viewing and editing image and text datasets. It's designed to streamline the process of reviewing and cleaning up datasets for AI and machine learning projects.

<img width="2533" height="763" alt="image" src="https://github.com/user-attachments/assets/f26f6f39-5052-413c-82b4-b648c3e8d0a9" />


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
* Tested with Python 3.12
It may work with other versions as well.

## Setup
1. Create a virtual environment. You may use the included `venv_create.bat` to automatically create it on Windows.
2. Install the libraries in requirements.txt. `pip install -r requirements.txt`. This is done by step 1 when asked if you use `venv_create`.


## How to use
1. Activate the virtual environment. If you installed with `venv_create.bat`, you can run `venv_activate.bat`.
2. Run `python batch.py` from the virtual environment.



## How to Use

1.  **Activate Environment:** Run `venv_activate.bat`.
2.  **Run Application:** Execute the main application script:
    ```bash
    python app.py
    ```
3.  **Open Folder:** Use the "Open Folder" button to select the root directory of your dataset.
4.  **Navigate and Edit:** Click on files in the list to view them. Text files can be edited in the text panel. Use the "Tools" menu for advanced editing options.


