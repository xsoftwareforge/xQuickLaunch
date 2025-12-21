#!/usr/bin/env python3
"""
QuickLaunch - Schnellstart-Leiste für Windows/Linux
Eine moderne Desktop-App zum Verwalten von Verknüpfungen
"""

import sys
# FreeBSD Fix: tkinterdnd2 needs 'linux' to pass checks, but psutil needs 'freebsd' to load correct C ext.
# Solution: Mock platform just long enough to load tkinterdnd2.
original_platform = sys.platform
if original_platform.startswith('freebsd'):
    sys.platform = 'linux'
    try:
        import tkinterdnd2
        # Force it to load and cache its platform checks now
    except ImportError:
        pass
    sys.platform = original_platform

from app import main

if __name__ == "__main__":
    main()
