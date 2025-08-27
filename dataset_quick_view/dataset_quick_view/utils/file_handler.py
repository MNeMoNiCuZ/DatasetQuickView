import os
from collections import defaultdict
from .config_manager import ConfigManager

def get_enabled_media_extensions():
    config = ConfigManager()
    supported_formats = config.get_setting('MediaFormats', 'supported', fallback='.png,.jpg,.jpeg,.bmp,.webp,.gif,.mp4')
    enabled_extensions = []
    for fmt in supported_formats.split(','):
        fmt = fmt.strip()
        if not fmt:
            continue
        if config.get_bool_setting('MediaFormats', fmt.replace('.', ''), fallback=True):
            enabled_extensions.append(fmt)
    return enabled_extensions

def is_media_file(filename):
    """Checks if a file is a media file based on its extension."""
    enabled_extensions = get_enabled_media_extensions()
    return any(filename.lower().endswith(ext) for ext in enabled_extensions)

def find_dataset_files(folder_path, recursive=True):
    """Scans a folder to group media files with their associated text files."""
    if not os.path.isdir(folder_path):
        return {}

    files_by_basename = defaultdict(list)
    
    if recursive:
        for root, _dirs, files in os.walk(folder_path):
            for filename in files:
                basename, _ = os.path.splitext(filename)
                full_path = os.path.join(root, filename)
                files_by_basename[os.path.join(root, basename)].append(full_path)
    else:
        for filename in os.listdir(folder_path):
            full_path = os.path.join(folder_path, filename)
            if os.path.isfile(full_path):
                basename, _ = os.path.splitext(filename)
                files_by_basename[os.path.join(folder_path, basename)].append(full_path)

    dataset = {}
    for _base_path, paths in files_by_basename.items():
        media_files = [p for p in paths if is_media_file(p)]
        text_files = [p for p in paths if not is_media_file(p)]

        # If multiple media files share a basename (e.g., cat.jpg, cat.png),
        # treat them as separate dataset items, each associated with all text files.
        if media_files and text_files:
            for media_file in media_files:
                dataset[media_file] = sorted(text_files)
        # If there are media files but no text files, still add them.
        elif media_files:
            for media_file in media_files:
                dataset[media_file] = []

    return dataset
