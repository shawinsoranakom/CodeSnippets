def site_config_dir(appname=None, appauthor=None, version=None, multipath=False):
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
        which indicates that the entire list of config dirs should be
        returned. By default, the first item from ``XDG_CONFIG_DIRS`` is
        returned, or :samp:`/etc/xdg/{AppName}`, if ``XDG_CONFIG_DIRS`` is not set

    Typical user data directories are:

    Mac OS X
        same as site_data_dir
    Unix
        ``/etc/xdg/<AppName>`` or ``$XDG_CONFIG_DIRS[i]/<AppName>`` for each
        value in ``$XDG_CONFIG_DIRS``
    Win *
        same as site_data_dir
    Vista
        Fail! "C:\ProgramData" is a hidden *system* directory on Vista.

    For Unix, this is using the ``$XDG_CONFIG_DIRS[0]`` default, if ``multipath=False``

    WARNING: Do not use this on Windows. See the Vista-Fail note above for why.
    """
    if sys.platform in [ "win32", "darwin" ]:
        path = site_data_dir(appname, appauthor)
        if appname and version:
            path = os.path.join(path, version)
    else:
        # XDG default for $XDG_CONFIG_DIRS
        # only first, if multipath is False
        path = os.getenv('XDG_CONFIG_DIRS', '/etc/xdg')
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