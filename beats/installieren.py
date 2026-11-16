"""Kopiert die Cole-Skripte in den FL-Studio-Ordner (Windows + Mac).

Doppelklick auf Installieren.bat (Windows) oder: python3 installieren.py
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'dist', 'Piano roll scripts')


def fl_settings_dirs():
    home = os.path.expanduser('~')
    cands = [
        os.path.join(home, 'Documents', 'Image-Line', 'FL Studio', 'Settings'),
        os.path.join(home, 'OneDrive', 'Documents', 'Image-Line', 'FL Studio', 'Settings'),
        os.path.join(home, 'OneDrive', 'Dokumente', 'Image-Line', 'FL Studio', 'Settings'),
        os.path.join(home, 'Dokumente', 'Image-Line', 'FL Studio', 'Settings'),
    ]
    return [c for c in cands if os.path.isdir(c)]


def main():
    if not os.path.isdir(SRC):
        print('dist/ fehlt - erst "python3 build.py" ausfuehren.')
        return 1
    dirs = fl_settings_dirs()
    if len(sys.argv) > 1:
        dirs = [sys.argv[1]]
    if not dirs:
        print('FL-Studio-Ordner nicht gefunden. Pfad angeben, z. B.:')
        print('  python installieren.py "C:\\Users\\DU\\Documents\\Image-Line\\FL Studio\\Settings"')
        return 1
    for d in dirs:
        target = os.path.join(d, 'Piano roll scripts')
        os.makedirs(target, exist_ok=True)
        for f in sorted(os.listdir(SRC)):
            shutil.copy2(os.path.join(SRC, f), os.path.join(target, f))
            print('installiert:', f)
        print('-> fertig in', target)
    print('\nIn FL Studio: Piano Roll oeffnen > oben links Menue > Tools > Scripting > "Cole - ..."')
    return 0


if __name__ == '__main__':
    sys.exit(main())
