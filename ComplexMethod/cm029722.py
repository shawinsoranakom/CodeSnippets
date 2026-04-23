def chown(path, user=None, group=None, *, dir_fd=None, follow_symlinks=True):
    """Change owner user and group of the given path.

    user and group can be the uid/gid or the user/group names, and in that case,
    they are converted to their respective uid/gid.

    If dir_fd is set, it should be an open file descriptor to the directory to
    be used as the root of *path* if it is relative.

    If follow_symlinks is set to False and the last element of the path is a
    symbolic link, chown will modify the link itself and not the file being
    referenced by the link.
    """
    sys.audit('shutil.chown', path, user, group)

    if user is None and group is None:
        raise ValueError("user and/or group must be set")

    _user = user
    _group = group

    # -1 means don't change it
    if user is None:
        _user = -1
    # user can either be an int (the uid) or a string (the system username)
    elif isinstance(user, str):
        _user = _get_uid(user)
        if _user is None:
            raise LookupError("no such user: {!r}".format(user))

    if group is None:
        _group = -1
    elif not isinstance(group, int):
        _group = _get_gid(group)
        if _group is None:
            raise LookupError("no such group: {!r}".format(group))

    os.chown(path, _user, _group, dir_fd=dir_fd,
             follow_symlinks=follow_symlinks)