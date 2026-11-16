"""Baut die FL-Studio Piano-Roll-Skripte (.pyscript) aus src/ nach dist/.

    python3 beats/build.py
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
OUT = os.path.join(HERE, 'dist', 'Piano roll scripts')
SCRIPTS = ['drums.py', 'akkorde.py', 'melodie.py', 'bass808.py', 'sample_chops.py', 'humanize.py']


def build_one(name):
    with open(os.path.join(SRC, 'core.py'), encoding='utf-8') as f:
        core = f.read()
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        body = f.read()
    title = next(l.split(':', 1)[1].strip() for l in body.splitlines() if l.startswith('# TITLE:'))
    text = ('# Cole Beats - automatisch gebaut aus beats/src/%s, nicht direkt bearbeiten.\n'
            'import flpianoroll as flp\n\n%s\n\n%s' % (name, core, body))
    return title, text


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in SCRIPTS:
        title, text = build_one(name)
        path = os.path.join(OUT, title + '.pyscript')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print('gebaut:', os.path.relpath(path, HERE))
    # Handy-Studio fuer GitHub Pages (docs/studio.html)
    docs = os.path.join(os.path.dirname(HERE), 'docs')
    if os.path.isdir(docs):
        shutil.copy(os.path.join(HERE, 'web', 'studio.html'), os.path.join(docs, 'studio.html'))
        print('gebaut: ../docs/studio.html')


if __name__ == '__main__':
    main()
