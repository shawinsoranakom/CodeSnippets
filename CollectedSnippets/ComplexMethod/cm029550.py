def checkEnvironment():
    """
    Check that we're running on a supported system.
    """

    if sys.version_info[0:2] < (2, 7):
        fatal("This script must be run with Python 2.7 (or later)")

    if platform.system() != 'Darwin':
        fatal("This script should be run on a macOS 10.5 (or later) system")

    if int(platform.release().split('.')[0]) < 8:
        fatal("This script should be run on a macOS 10.5 (or later) system")

    # Because we only support dynamic load of only one major/minor version of
    # Tcl/Tk, if we are not using building and using our own private copy of
    # Tcl/Tk, ensure:
    # 1. there is a user-installed framework (usually ActiveTcl) in (or linked
    #       in) SDKROOT/Library/Frameworks.  As of Python 3.7.0, we no longer
    #       enforce that the version of the user-installed framework also
    #       exists in the system-supplied Tcl/Tk frameworks.  Time to support
    #       Tcl/Tk 8.6 even if Apple does not.
    if not internalTk():
        frameworks = {}
        for framework in ['Tcl', 'Tk']:
            fwpth = 'Library/Frameworks/%s.framework/Versions/Current' % framework
            libfw = os.path.join('/', fwpth)
            usrfw = os.path.join(os.getenv('HOME'), fwpth)
            frameworks[framework] = os.readlink(libfw)
            if not os.path.exists(libfw):
                fatal("Please install a link to a current %s %s as %s so "
                        "the user can override the system framework."
                        % (framework, frameworks[framework], libfw))
            if os.path.exists(usrfw):
                fatal("Please rename %s to avoid possible dynamic load issues."
                        % usrfw)

        if frameworks['Tcl'] != frameworks['Tk']:
            fatal("The Tcl and Tk frameworks are not the same version.")

        print(" -- Building with external Tcl/Tk %s frameworks"
                    % frameworks['Tk'])

        # add files to check after build
        EXPECTED_SHARED_LIBS['_tkinter.so'] = [
                "/Library/Frameworks/Tcl.framework/Versions/%s/Tcl"
                    % frameworks['Tcl'],
                "/Library/Frameworks/Tk.framework/Versions/%s/Tk"
                    % frameworks['Tk'],
                ]
    else:
        print(" -- Building private copy of Tcl/Tk")
    print("")

    # Remove inherited environment variables which might influence build
    environ_var_prefixes = ['CPATH', 'C_INCLUDE_', 'DYLD_', 'LANG', 'LC_',
                            'LD_', 'LIBRARY_', 'PATH', 'PYTHON']
    for ev in list(os.environ):
        for prefix in environ_var_prefixes:
            if ev.startswith(prefix) :
                print("INFO: deleting environment variable %s=%s" % (
                                                    ev, os.environ[ev]))
                del os.environ[ev]

    base_path = '/bin:/sbin:/usr/bin:/usr/sbin'
    if 'SDK_TOOLS_BIN' in os.environ:
        base_path = os.environ['SDK_TOOLS_BIN'] + ':' + base_path
    # Xcode 2.5 on OS X 10.4 does not include SetFile in its usr/bin;
    # add its fixed location here if it exists
    OLD_DEVELOPER_TOOLS = '/Developer/Tools'
    if os.path.isdir(OLD_DEVELOPER_TOOLS):
        base_path = base_path + ':' + OLD_DEVELOPER_TOOLS
    os.environ['PATH'] = base_path
    print("Setting default PATH: %s"%(os.environ['PATH']))