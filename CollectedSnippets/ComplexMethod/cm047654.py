def site_data_dir(appname=None, appauthor=None, version=None, multipath=False):
    r"""Return full path to the user-shared data dir for this application.

        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only required and used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "multipath" is an optional parameter only applicable to \*nix
            which indicates that the entire list of data dirs should be
            returned. By default, the first item from XDG_DATA_DIRS is
            returned, or :samp:`/usr/local/share/{AppName}`,
            if ``XDG_DATA_DIRS`` is not set

    Typical user data directories are:

    Mac OS X
        :samp:`/Library/Application Support/{AppName}`
    Unix
        :samp:`/usr/local/share/{AppName}` or :samp:`/usr/share/{AppName}`
    Win XP
        :samp:`C:\Documents and Settings\All Users\Application Data\{AppAuthor}\{AppName}`
    Vista
        Fail! "C:\ProgramData" is a hidden *system* directory on Vista.
    Win 7
        :samp:`C:\ProgramData\{AppAuthor}\{AppName}` (hidden, but writeable on Win 7)

    For Unix, this is using the ``$XDG_DATA_DIRS[0]`` default.

    WARNING: Do not use this on Windows. See the Vista-Fail note above for why.
    """
    if sys.platform == "win32":
        if appauthor is None:
            appauthor = appname
        path = os.path.normpath(_get_win_folder("CSIDL_COMMON_APPDATA"))
        if appname:
            path = os.path.join(path, appauthor, appname)
    elif sys.platform == 'darwin':
        path = os.path.expanduser('/Library/Application Support')
        if appname:
            path = os.path.join(path, appname)
    else:
        # XDG default for $XDG_DATA_DIRS
        # only first, if multipath is False
        path = os.getenv('XDG_DATA_DIRS',
                        os.pathsep.join(['/usr/local/share', '/usr/share']))
        pathlist = [ os.path.expanduser(x.rstrip(os.sep)) for x in path.split(os.pathsep) ]
        if appname:
            if version:
                appname = os.path.join(appname, version)
            pathlist = [ os.sep.join([x, appname]) for x in pathlist ]

        if multipath:
            path = os.pathsep.join(pathlist)
        else:
            path = pathlist[0]
        return path

    if appname and version:
        path = os.path.join(path, version)
    return path