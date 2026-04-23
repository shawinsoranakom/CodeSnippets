def register_standard_browsers():
    global _tryorder
    _tryorder = []

    if sys.platform == 'darwin':
        register("MacOSX", None, MacOSXOSAScript('default'))
        register("chrome", None, MacOSXOSAScript('google chrome'))
        register("firefox", None, MacOSXOSAScript('firefox'))
        register("safari", None, MacOSXOSAScript('safari'))
        # macOS can use below Unix support (but we prefer using the macOS
        # specific stuff)

    if sys.platform == "ios":
        register("iosbrowser", None, IOSBrowser(), preferred=True)

    if sys.platform == "serenityos":
        # SerenityOS webbrowser, simply called "Browser".
        register("Browser", None, BackgroundBrowser("Browser"))

    if sys.platform[:3] == "win":
        # First try to use the default Windows browser
        register("windows-default", WindowsDefault)

        # Detect some common Windows browsers, fallback to Microsoft Edge
        # location in 64-bit Windows
        edge64 = os.path.join(os.environ.get("PROGRAMFILES(x86)", "C:\\Program Files (x86)"),
                              "Microsoft\\Edge\\Application\\msedge.exe")
        # location in 32-bit Windows
        edge32 = os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                              "Microsoft\\Edge\\Application\\msedge.exe")
        for browser in ("firefox", "seamonkey", "mozilla", "chrome",
                        "opera", edge64, edge32):
            if shutil.which(browser):
                register(browser, None, BackgroundBrowser(browser))
        if shutil.which("MicrosoftEdge.exe"):
            register("microsoft-edge", None, Edge("MicrosoftEdge.exe"))
    else:
        # Prefer X browsers if present
        #
        # NOTE: Do not check for X11 browser on macOS,
        # XQuartz installation sets a DISPLAY environment variable and will
        # autostart when someone tries to access the display. Mac users in
        # general don't need an X11 browser.
        if sys.platform != "darwin" and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            try:
                cmd = "xdg-settings get default-web-browser".split()
                raw_result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                result = raw_result.decode().strip()
            except (FileNotFoundError, subprocess.CalledProcessError,
                    PermissionError, NotADirectoryError):
                pass
            else:
                global _os_preferred_browser
                _os_preferred_browser = result

            register_X_browsers()

        # Also try console browsers
        if os.environ.get("TERM"):
            # Common symbolic link for the default text-based browser
            if shutil.which("www-browser"):
                register("www-browser", None, GenericBrowser("www-browser"))
            # The Links/elinks browsers <http://links.twibright.com/>
            if shutil.which("links"):
                register("links", None, GenericBrowser("links"))
            if shutil.which("elinks"):
                register("elinks", None, Elinks("elinks"))
            # The Lynx browser <https://lynx.invisible-island.net/>, <http://lynx.browser.org/>
            if shutil.which("lynx"):
                register("lynx", None, GenericBrowser("lynx"))
            # The w3m browser <http://w3m.sourceforge.net/>
            if shutil.which("w3m"):
                register("w3m", None, GenericBrowser("w3m"))

    # OK, now that we know what the default preference orders for each
    # platform are, allow user to override them with the BROWSER variable.
    if "BROWSER" in os.environ:
        userchoices = os.environ["BROWSER"].split(os.pathsep)
        userchoices.reverse()

        # Treat choices in same way as if passed into get() but do register
        # and prepend to _tryorder
        for cmdline in userchoices:
            if all(x not in cmdline for x in " \t"):
                # Assume this is the name of a registered command, use
                # that unless it is a GenericBrowser.
                try:
                    command = _browsers[cmdline.lower()]
                except KeyError:
                    pass

                else:
                    if not isinstance(command[1], GenericBrowser):
                        _tryorder.insert(0, cmdline.lower())
                        continue

            if cmdline != '':
                cmd = _synthesize(cmdline, preferred=True)
                if cmd[1] is None:
                    register(cmdline, None, GenericBrowser(cmdline), preferred=True)