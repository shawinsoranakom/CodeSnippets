def msgfmt_version(self):
        # Note that msgfmt is installed via GNU gettext tools, hence the msgfmt
        # version should align to gettext.
        out, err, status = popen_wrapper(
            ["msgfmt", "--version"],
            stdout_encoding=DEFAULT_LOCALE_ENCODING,
        )
        m = re.search(r"(\d+)\.(\d+)\.?(\d+)?", out)
        return tuple(int(d) for d in m.groups() if d is not None)