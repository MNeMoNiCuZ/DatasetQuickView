import os
import sys
import subprocess
import ctypes
from ctypes import wintypes

def open_selected_file_directory(media_path):
    try:
        if sys.platform == "win32":
            normalized_path = os.path.normpath(media_path)
            
            class ITEMIDLIST(ctypes.Structure):
                pass
            
            ctypes.windll.shell32.ILCreateFromPathW.argtypes = [wintypes.LPCWSTR]
            ctypes.windll.shell32.ILCreateFromPathW.restype = ctypes.POINTER(ITEMIDLIST)
            
            ctypes.windll.shell32.SHOpenFolderAndSelectItems.argtypes = [
                ctypes.POINTER(ITEMIDLIST),
                wintypes.UINT,
                ctypes.POINTER(ctypes.POINTER(ITEMIDLIST)),
                wintypes.DWORD
            ]
            
            pidl = ctypes.windll.shell32.ILCreateFromPathW(normalized_path)
            if pidl:
                try:
                    ctypes.windll.shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
                finally:
                    ctypes.windll.shell32.ILFree(pidl)

        elif sys.platform == "darwin":
            subprocess.Popen(['open', '-R', media_path])
        else:
            directory = os.path.dirname(media_path)
            subprocess.Popen(['xdg-open', directory])
    except Exception as e:
        # This should be handled by the caller
        raise e
