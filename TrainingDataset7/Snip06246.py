def get_system_username():
    """
    Return the current system user's username, or an empty string if the
    username could not be determined.
    """
    try:
        result = getpass.getuser()
    except (ImportError, KeyError, OSError):
        # TODO: Drop ImportError and KeyError when dropping support for PY312.
        # KeyError (Python <3.13) or OSError (Python 3.13+) will be raised by
        # os.getpwuid() (called by getuser()) if there is no corresponding
        # entry in the /etc/passwd file (for example, in a very restricted
        # chroot environment).
        return ""
    return result