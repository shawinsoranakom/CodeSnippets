def main():
    import getopt
    from platform import system
    from idlelib import testing  # bool value
    from idlelib import macosx

    global flist, root, use_subprocess

    capture_warnings(True)
    use_subprocess = True
    enable_shell = False
    enable_edit = False
    debug = False
    cmd = None
    script = None
    startup = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:deihnr:st:")
    except getopt.error as msg:
        print(f"Error: {msg}\n{usage_msg}", file=sys.stderr)
        sys.exit(2)
    for o, a in opts:
        if o == '-c':
            cmd = a
            enable_shell = True
        if o == '-d':
            debug = True
            enable_shell = True
        if o == '-e':
            enable_edit = True
        if o == '-h':
            sys.stdout.write(usage_msg)
            sys.exit()
        if o == '-i':
            enable_shell = True
        if o == '-n':
            print(" Warning: running IDLE without a subprocess is deprecated.",
                  file=sys.stderr)
            use_subprocess = False
        if o == '-r':
            script = a
            if os.path.isfile(script):
                pass
            else:
                print("No script file: ", script)
                sys.exit()
            enable_shell = True
        if o == '-s':
            startup = True
            enable_shell = True
        if o == '-t':
            PyShell.shell_title = a
            enable_shell = True
    if args and args[0] == '-':
        cmd = sys.stdin.read()
        enable_shell = True
    # process sys.argv and sys.path:
    for i in range(len(sys.path)):
        sys.path[i] = os.path.abspath(sys.path[i])
    if args and args[0] == '-':
        sys.argv = [''] + args[1:]
    elif cmd:
        sys.argv = ['-c'] + args
    elif script:
        sys.argv = [script] + args
    elif args:
        enable_edit = True
        pathx = []
        for filename in args:
            pathx.append(os.path.dirname(filename))
        for dir in pathx:
            dir = os.path.abspath(dir)
            if not dir in sys.path:
                sys.path.insert(0, dir)
    else:
        dir = os.getcwd()
        if dir not in sys.path:
            sys.path.insert(0, dir)
    # check the IDLE settings configuration (but command line overrides)
    edit_start = idleConf.GetOption('main', 'General',
                                    'editor-on-startup', type='bool')
    enable_edit = enable_edit or edit_start
    enable_shell = enable_shell or not enable_edit

    # Setup root.  Don't break user code run in IDLE process.
    # Don't change environment when testing.
    if use_subprocess and not testing:
        NoDefaultRoot()
    root = Tk(className="Idle")
    root.withdraw()
    from idlelib.run import fix_scaling
    fix_scaling(root)

    # set application icon
    icondir = os.path.join(os.path.dirname(__file__), 'Icons')
    if system() == 'Windows':
        iconfile = os.path.join(icondir, 'idle.ico')
        root.wm_iconbitmap(default=iconfile)
    elif not macosx.isAquaTk():
        if TkVersion >= 8.6:
            ext = '.png'
            sizes = (16, 32, 48, 256)
        else:
            ext = '.gif'
            sizes = (16, 32, 48)
        iconfiles = [os.path.join(icondir, 'idle_%d%s' % (size, ext))
                     for size in sizes]
        icons = [PhotoImage(master=root, file=iconfile)
                 for iconfile in iconfiles]
        root.wm_iconphoto(True, *icons)

    # start editor and/or shell windows:
    fixwordbreaks(root)
    fix_x11_paste(root)
    flist = PyShellFileList(root)
    macosx.setupApp(root, flist)

    if enable_edit:
        if not (cmd or script):
            for filename in args[:]:
                if flist.open(filename) is None:
                    # filename is a directory actually, disconsider it
                    args.remove(filename)
            if not args:
                flist.new()

    if enable_shell:
        shell = flist.open_shell()
        if not shell:
            return # couldn't open shell
        if macosx.isAquaTk() and flist.dict:
            # On OSX: when the user has double-clicked on a file that causes
            # IDLE to be launched the shell window will open just in front of
            # the file she wants to see. Lower the interpreter window when
            # there are open files.
            shell.top.lower()
    else:
        shell = flist.pyshell

    # Handle remaining options. If any of these are set, enable_shell
    # was set also, so shell must be true to reach here.
    if debug:
        shell.open_debugger()
    if startup:
        filename = os.environ.get("IDLESTARTUP") or \
                   os.environ.get("PYTHONSTARTUP")
        if filename and os.path.isfile(filename):
            shell.interp.execfile(filename)
    if cmd or script:
        shell.interp.runcommand("""if 1:
            import sys as _sys
            _sys.argv = {!r}
            del _sys
            \n""".format(sys.argv))
        if cmd:
            shell.interp.execsource(cmd)
        elif script:
            shell.interp.prepend_syspath(script)
            shell.interp.execfile(script)
    elif shell:
        # If there is a shell window and no cmd or script in progress,
        # check for problematic issues and print warning message(s) in
        # the IDLE shell window; this is less intrusive than always
        # opening a separate window.

        # Warn if the "Prefer tabs when opening documents" system
        # preference is set to "Always".
        prefer_tabs_preference_warning = macosx.preferTabsPreferenceWarning()
        if prefer_tabs_preference_warning:
            shell.show_warning(prefer_tabs_preference_warning)

    while flist.inversedict:  # keep IDLE running while files are open.
        root.mainloop()
    root.destroy()
    capture_warnings(False)