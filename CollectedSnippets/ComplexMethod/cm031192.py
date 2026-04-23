def available_timezones():
    """Returns a set containing all available time zones.

    .. caution::

        This may attempt to open a large number of files, since the best way to
        determine if a given file on the time zone search path is to open it
        and check for the "magic string" at the beginning.
    """
    from importlib import resources

    valid_zones = set()

    # Start with loading from the tzdata package if it exists: this has a
    # pre-assembled list of zones that only requires opening one file.
    try:
        zones_file = resources.files("tzdata").joinpath("zones")
        with zones_file.open("r", encoding="utf-8") as f:
            for zone in f:
                zone = zone.strip()
                if zone:
                    valid_zones.add(zone)
    except (ImportError, FileNotFoundError):
        pass

    def valid_key(fpath):
        try:
            with open(fpath, "rb") as f:
                return f.read(4) == b"TZif"
        except Exception:  # pragma: nocover
            return False

    for tz_root in TZPATH:
        if not os.path.exists(tz_root):
            continue

        for root, dirnames, files in os.walk(tz_root):
            if root == tz_root:
                # right/ and posix/ are special directories and shouldn't be
                # included in the output of available zones
                if "right" in dirnames:
                    dirnames.remove("right")
                if "posix" in dirnames:
                    dirnames.remove("posix")

            for file in files:
                fpath = os.path.join(root, file)

                key = os.path.relpath(fpath, start=tz_root)
                if os.sep != "/":  # pragma: nocover
                    key = key.replace(os.sep, "/")

                if not key or key in valid_zones:
                    continue

                if valid_key(fpath):
                    valid_zones.add(key)

    if "posixrules" in valid_zones:
        # posixrules is a special symlink-only time zone where it exists, it
        # should not be included in the output
        valid_zones.remove("posixrules")
    if "localtime" in valid_zones:
        # localtime is a special symlink-only time zone where it exists, it
        # should not be included in the output
        valid_zones.remove("localtime")

    return valid_zones