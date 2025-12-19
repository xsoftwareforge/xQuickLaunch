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
        _fields_ = [("fIcon", ctypes.c_bool),
                    ("xHotspot", wintypes.DWORD),
                    ("yHotspot", wintypes.DWORD),
                    ("hbmMask", wintypes.HBITMAP),
                    ("hbmColor", wintypes.HBITMAP)]

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
        _fields_ = [("hIcon", wintypes.HICON),
                    ("iIcon", ctypes.c_int),
                    ("dwAttributes", wintypes.DWORD),
                    ("szDisplayName", ctypes.c_wchar * 260),
                    ("szTypeName", ctypes.c_wchar * 80)]

    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    SHGFI_ICON = 0x000000100
    SHGFI_LARGEICON = 0x000000000 # Large icon is usually 32x32, we might want extra large but that requires specific API
    # 0x0 is SHGFI_LARGEICON, 0x1 is SHGFI_SMALLICON
    
    DIB_RGB_COLORS = 0

def get_file_icon_path(file_path: str, cache_dir: str) -> str:
    """
    Extracts icon from file and saves to cache_dir.
    Returns path to cached png.
    If extraction fails or not Windows, returns None or original path if it's an image.
    """
    path = Path(file_path)
    if not path.exists():
        return None
        
    # If it is already an image, return it
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
        
        # GetDIBits
        # Note: We should ideally use icon_info.hbmColor, but GetIconInfo might return a compatible bitmap, not a DIB.
        # We need to draw the icon into a DIB to get the alpha channel properly if simpler methods fail, 
        # but often GetDIBits on the hbmColor works if it exists. 
        # However, icons often have complex masks. 
        # Simplest valid way for simple extraction: DrawIconEx into a CreateDIBSection.
        
        h_bitmap = gdi32.CreateDIBSection(mem_dc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(ctypes.c_void_p()), 0, 0)
        if not h_bitmap:
            user32.ReleaseDC(0, hdc)
            user32.DestroyIcon(hIcon)
            return None

        old_bitmap = gdi32.SelectObject(mem_dc, h_bitmap)
        
        # Draw icon
        # DrawIconEx(hdc, xLeft, yTop, hIcon, cxWidth, cyWidth, istepIfAniCur, hbrFlickerFreeDraw, diFlags)
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
