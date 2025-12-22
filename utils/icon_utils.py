import ctypes
import sys
from ctypes import wintypes
from PIL import Image
import os
import hashlib
from pathlib import Path

# Only define Windows structs if on Windows
if sys.platform == "win32":
    class ICONINFO(ctypes.Structure):
        _fields_ = [("fIcon", ctypes.c_int), # BOOL is int
                    ("xHotspot", wintypes.DWORD),
                    ("yHotspot", wintypes.DWORD),
                    ("hbmMask", ctypes.c_void_p), # HBITMAP
                    ("hbmColor", ctypes.c_void_p)] # HBITMAP

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD),
                    ("biWidth", ctypes.c_long),
                    ("biHeight", ctypes.c_long),
                    ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long),
                    ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                    ("bmiColors", wintypes.DWORD * 3)]

    class SHFILEINFOW(ctypes.Structure):
        _fields_ = [("hIcon", ctypes.c_void_p), # HICON
                    ("iIcon", ctypes.c_int),
                    ("dwAttributes", wintypes.DWORD),
                    ("szDisplayName", ctypes.c_wchar * 260),
                    ("szTypeName", ctypes.c_wchar * 80)]

    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    # Define argtypes and restypes to prevent 64-bit overflow errors
    
    # SHGetFileInfoW
    # DWORD_PTR SHGetFileInfoW(LPCWSTR pszPath, DWORD dwFileAttributes, SHFILEINFOW *psfi, UINT cbFileInfo, UINT uFlags);
    shell32.SHGetFileInfoW.argtypes = [ctypes.c_wchar_p, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW), wintypes.UINT, wintypes.UINT]
    shell32.SHGetFileInfoW.restype = ctypes.c_void_p # DWORD_PTR is 64-bit

    # GetIconInfo
    # BOOL GetIconInfo(HICON hIcon, PICONINFO piconinfo);
    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(ICONINFO)]
    user32.GetIconInfo.restype = wintypes.BOOL
    
    # DestroyIcon
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.DestroyIcon.restype = wintypes.BOOL
    
    # GetDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    
    # CreateCompatibleDC
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    
    # CreateDIBSection
    gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
    gdi32.CreateDIBSection.restype = wintypes.HBITMAP
    
    # SelectObject
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ # Returns HGDIOBJ (Handle)
    
    # DrawIconEx
    # BOOL DrawIconEx(HDC hdc, int xLeft, int yTop, HICON hIcon, int cxWidth, int cyWidth, UINT istepIfAniCur, HBRUSH hbrFlickerFreeDraw, UINT diFlags);
    user32.DrawIconEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.HICON, ctypes.c_int, ctypes.c_int, wintypes.UINT, wintypes.HBRUSH, wintypes.UINT]
    user32.DrawIconEx.restype = wintypes.BOOL
    
    # GetDIBits
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.POINTER(BITMAPINFO), wintypes.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int
    
    # ReleaseDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    
    # DeleteDC
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL
    
    # DeleteObject
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL

    SHGFI_ICON = 0x000000100
    SHGFI_LARGEICON = 0x000000000
    
    DIB_RGB_COLORS = 0

def get_file_icon_path(file_path: str, cache_dir: str) -> str:
    """
    Extracts icon from file and saves to cache_dir.
    Returns path to cached png.
    """
    path = Path(file_path)
    if not path.exists():
        return None
        
    # If it is already an image, return it
    if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.ico']:
        return str(path)
        
    # Resolve LNK if on Windows
    # Import here to avoid circular dependency if possible, or assume it's available
    from utils.system_utils import resolve_lnk_path
    
    # Try to resolve LNK to get original file for better icon
    resolved_path = resolve_lnk_path(str(path))
    if resolved_path != str(path):
        # Update path to target for extraction
        path = Path(resolved_path)
    
    # If resolved path is an image, return it
    if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.ico']:
        return str(path)

    # Generate hash for cache filename
    file_hash = hashlib.md5(str(path).encode('utf-8')).hexdigest()
    cache_path = Path(cache_dir) / f"{file_hash}.png"
    
    if cache_path.exists():
        return str(cache_path)
        
    if sys.platform != "win32":
        return None
        
    try:
        # Get HICON
        shfileinfo = SHFILEINFOW()
        # SHGFI_ICON | SHGFI_LARGEICON (0)
        ret = shell32.SHGetFileInfoW(
            str(path),
            0,
            ctypes.byref(shfileinfo),
            ctypes.sizeof(shfileinfo),
            SHGFI_ICON | SHGFI_LARGEICON
        )
        
        if ret == 0 or not shfileinfo.hIcon:
            return None
            
        hIcon = shfileinfo.hIcon
        
        # Get Icon Info
        icon_info = ICONINFO()
        if not user32.GetIconInfo(hIcon, ctypes.byref(icon_info)):
            user32.DestroyIcon(hIcon)
            return None
            
        w = 32 # Default large icon size
        h = 32
        
        # We need to get the bitmap bits
        hdc = user32.GetDC(0)
        mem_dc = gdi32.CreateCompatibleDC(hdc)
        
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = w
        bmi.bmiHeader.biHeight = -h # Top-down
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0 # BI_RGB
        
        # Determine strict buffer size
        buffer_len = w * h * 4
        buffer = ctypes.create_string_buffer(buffer_len)
        
        h_bitmap = gdi32.CreateDIBSection(mem_dc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(ctypes.c_void_p()), 0, 0)
        if not h_bitmap:
            user32.ReleaseDC(0, hdc)
            user32.DestroyIcon(hIcon)
            return None

        old_bitmap = gdi32.SelectObject(mem_dc, h_bitmap)
        
        # Draw icon
        DI_NORMAL = 0x0003
        user32.DrawIconEx(mem_dc, 0, 0, hIcon, w, h, 0, 0, DI_NORMAL)
        
        # Get bits
        gdi32.GetDIBits(mem_dc, h_bitmap, 0, h, buffer, ctypes.byref(bmi), DIB_RGB_COLORS)
        
        # Creating PIL Image
        # BGRA to RGBA
        image = Image.frombuffer("RGBA", (w, h), buffer, "raw", "BGRA", 0, 1)
        
        # Clean up
        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(h_bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(0, hdc)
        user32.DestroyIcon(hIcon)
        if icon_info.hbmColor: gdi32.DeleteObject(icon_info.hbmColor)
        if icon_info.hbmMask: gdi32.DeleteObject(icon_info.hbmMask)
        
        # Save
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        image.save(cache_path)
        return str(cache_path)
        
    except Exception as e:
        print(f"Icon extraction failed: {e}")
        return None
