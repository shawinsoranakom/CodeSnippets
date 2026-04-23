def _rmtree_unsafe(path, dir_fd, onexc):
    if dir_fd is not None:
        raise NotImplementedError("dir_fd unavailable on this platform")
    try:
        st = os.lstat(path)
    except OSError as err:
        onexc(os.lstat, path, err)
        return
    try:
        if _rmtree_islink(st):
            # symlinks to directories are forbidden, see bug #1669
            raise OSError("Cannot call rmtree on a symbolic link")
    except OSError as err:
        onexc(os.path.islink, path, err)
        # can't continue even if onexc hook returns
        return
    def onerror(err):
        if not isinstance(err, FileNotFoundError):
            onexc(os.scandir, err.filename, err)
    results = os.walk(path, topdown=False, onerror=onerror, followlinks=os._walk_symlinks_as_files)
    for dirpath, dirnames, filenames in results:
        for name in dirnames:
            fullname = os.path.join(dirpath, name)
            try:
                os.rmdir(fullname)
            except FileNotFoundError:
                continue
            except OSError as err:
                onexc(os.rmdir, fullname, err)
        for name in filenames:
            fullname = os.path.join(dirpath, name)
            try:
                os.unlink(fullname)
            except FileNotFoundError:
                continue
            except OSError as err:
                onexc(os.unlink, fullname, err)
    try:
        os.rmdir(path)
    except FileNotFoundError:
        pass
    except OSError as err:
        onexc(os.rmdir, path, err)