#!/usr/bin/env python3
"""
QuickLaunch - Schnellstart-Leiste für Windows/Linux
Eine moderne Desktop-App zum Verwalten von Verknüpfungen
"""

import sys
# FreeBSD Fix: tkinterdnd2 and some other libs have strict platform checks
# We mock 'linux' because FreeBSD works similarly for X11/Tk
if sys.platform.startswith('freebsd'):
    sys.platform = 'linux'

from app import main

if __name__ == "__main__":
    main()
