def main():
    import os
    import re
    import shutil
    import sys
    dests = sys.argv[1:] or ['.']
    filename = re.sub(r'\.pyc$', '.py', __file__)

    for dst in dests:
        shutil.copy(filename, dst)
        manifest_path = os.path.join(dst, 'MANIFEST.in')
        setup_path = os.path.join(dst, 'setup.py')

        # Insert the include statement to MANIFEST.in if not present
        with open(manifest_path, 'a+') as manifest:
            manifest.seek(0)
            manifest_content = manifest.read()
            if not 'include fastentrypoints.py' in manifest_content:
                manifest.write(('\n' if manifest_content else '')
                               + 'include fastentrypoints.py')

        # Insert the import statement to setup.py if not present
        with open(setup_path, 'a+') as setup:
            setup.seek(0)
            setup_content = setup.read()
            if not 'import fastentrypoints' in setup_content:
                setup.seek(0)
                setup.truncate()
                setup.write('import fastentrypoints\n' + setup_content)