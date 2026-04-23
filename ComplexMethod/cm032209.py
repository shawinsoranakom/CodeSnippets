def default_download_dir(self):
        """
        Return the directory to which packages will be downloaded by
        default.  This value can be overridden using the constructor,
        or on a case-by-case basis using the ``download_dir`` argument when
        calling ``download()``.

        On Windows, the default download directory is
        ``PYTHONHOME/lib/nltk``, where *PYTHONHOME* is the
        directory containing Python, e.g. ``C:\\Python25``.

        On all other platforms, the default directory is the first of
        the following which exists or which can be created with write
        permission: ``/usr/share/nltk_data``, ``/usr/local/share/nltk_data``,
        ``/usr/lib/nltk_data``, ``/usr/local/lib/nltk_data``, ``~/nltk_data``.
        """
        # Check if we are on GAE where we cannot write into filesystem.
        if "APPENGINE_RUNTIME" in os.environ:
            return

        # Check if we have sufficient permissions to install in a
        # variety of system-wide locations.
        for nltkdir in nltk.data.path:
            if os.path.exists(nltkdir) and nltk.internals.is_writable(nltkdir):
                return nltkdir

        # On Windows, use %APPDATA%
        if sys.platform == "win32" and "APPDATA" in os.environ:
            homedir = os.environ["APPDATA"]

        # Otherwise, install in the user's home directory.
        else:
            homedir = os.path.expanduser("~/")
            if homedir == "~/":
                raise ValueError("Could not find a default download directory")

        # append "nltk_data" to the home directory
        return os.path.join(homedir, "nltk_data")