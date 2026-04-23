def register_X_browsers():

    # use xdg-open if around
    if shutil.which("xdg-open"):
        register("xdg-open", None, BackgroundBrowser("xdg-open"))

    # Opens an appropriate browser for the URL scheme according to
    # freedesktop.org settings (GNOME, KDE, XFCE, etc.)
    if shutil.which("gio"):
        register("gio", None, BackgroundBrowser(["gio", "open", "--", "%s"]))

    xdg_desktop = os.getenv("XDG_CURRENT_DESKTOP", "").split(":")

    # The default GNOME3 browser
    if (("GNOME" in xdg_desktop or
         "GNOME_DESKTOP_SESSION_ID" in os.environ) and
            shutil.which("gvfs-open")):
        register("gvfs-open", None, BackgroundBrowser("gvfs-open"))

    # The default KDE browser
    if (("KDE" in xdg_desktop or
         "KDE_FULL_SESSION" in os.environ) and
            shutil.which("kfmclient")):
        register("kfmclient", Konqueror, Konqueror("kfmclient"))

    # Common symbolic link for the default X11 browser
    if shutil.which("x-www-browser"):
        register("x-www-browser", None, BackgroundBrowser("x-www-browser"))

    # The Mozilla browsers
    for browser in ("firefox", "iceweasel", "seamonkey", "mozilla-firefox",
                    "mozilla"):
        if shutil.which(browser):
            register(browser, None, Mozilla(browser))

    # Konqueror/kfm, the KDE browser.
    if shutil.which("kfm"):
        register("kfm", Konqueror, Konqueror("kfm"))
    elif shutil.which("konqueror"):
        register("konqueror", Konqueror, Konqueror("konqueror"))

    # Gnome's Epiphany
    if shutil.which("epiphany"):
        register("epiphany", None, Epiphany("epiphany"))

    # Google Chrome/Chromium browsers
    for browser in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        if shutil.which(browser):
            register(browser, None, Chrome(browser))

    # Opera, quite popular
    if shutil.which("opera"):
        register("opera", None, Opera("opera"))

    if shutil.which("microsoft-edge"):
        register("microsoft-edge", None, Edge("microsoft-edge"))