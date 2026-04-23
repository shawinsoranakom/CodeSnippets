def gettext_version(self):
        # Gettext tools will output system-encoded bytestrings instead of
        # UTF-8, when looking up the version. It's especially a problem on
        # Windows.
        out, err, status = popen_wrapper(
            ["xgettext", "--version"],
            stdout_encoding=DEFAULT_LOCALE_ENCODING,
        )
        m = re.search(r"(\d+)\.(\d+)\.?(\d+)?", out)
        if m:
            return tuple(int(d) for d in m.groups() if d is not None)
        else:
            raise CommandError("Unable to get gettext version. Is it installed?")