def _get_dochome():
    "Return path to local docs if present, otherwise link to docs.python.org."

    dochome = os.path.join(sys.base_prefix, 'Doc', 'index.html')
    if sys.platform.count('linux'):
        # look for html docs in a couple of standard places
        pyver = 'python-docs-' + '%s.%s.%s' % sys.version_info[:3]
        if os.path.isdir('/var/www/html/python/'):  # rpm package manager
            dochome = '/var/www/html/python/index.html'
        else:
            basepath = '/usr/share/doc/'  # dnf/apt package managers
            dochome = os.path.join(basepath, pyver, 'Doc', 'index.html')

    elif sys.platform[:3] == 'win':
        import winreg  # Windows only, block only executed once.
        docfile = ''
        KEY = (rf"Software\Python\PythonCore\{sys.winver}"
               r"\Help\Main Python Documentation")
        try:
            docfile = winreg.QueryValue(winreg.HKEY_CURRENT_USER, KEY)
        except FileNotFoundError:
            try:
                docfile = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE, KEY)
            except FileNotFoundError:
                pass
        if os.path.isfile(docfile):
            dochome = docfile
    elif sys.platform == 'darwin':
        # documentation may be stored inside a python framework
        dochome = os.path.join(sys.base_prefix,
                               'Resources/English.lproj/Documentation/index.html')
    dochome = os.path.normpath(dochome)
    if os.path.isfile(dochome):
        if sys.platform == 'darwin':
            # Safari requires real file:-URLs
            return 'file://' + dochome
        return dochome
    else:
        return "https://docs.python.org/%d.%d/" % sys.version_info[:2]