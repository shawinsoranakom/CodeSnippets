def _rmtree_safe_fd_step(stack, onexc):
    # Each stack item has four elements:
    # * func: The first operation to perform: os.lstat, os.close or os.rmdir.
    #   Walking a directory starts with an os.lstat() to detect symlinks; in
    #   this case, func is updated before subsequent operations and passed to
    #   onexc() if an error occurs.
    # * dirfd: Open file descriptor, or None if we're processing the top-level
    #   directory given to rmtree() and the user didn't supply dir_fd.
    # * path: Path of file to operate upon. This is passed to onexc() if an
    #   error occurs.
    # * orig_entry: os.DirEntry, or None if we're processing the top-level
    #   directory given to rmtree(). We used the cached stat() of the entry to
    #   save a call to os.lstat() when walking subdirectories.
    func, dirfd, path, orig_entry = stack.pop()
    name = path if orig_entry is None else orig_entry.name
    try:
        if func is os.close:
            os.close(dirfd)
            return
        if func is os.rmdir:
            os.rmdir(name, dir_fd=dirfd)
            return

        # Note: To guard against symlink races, we use the standard
        # lstat()/open()/fstat() trick.
        assert func is os.lstat
        if orig_entry is None:
            orig_st = os.lstat(name, dir_fd=dirfd)
        else:
            orig_st = orig_entry.stat(follow_symlinks=False)

        func = os.open  # For error reporting.
        topfd = os.open(name, os.O_RDONLY | os.O_NONBLOCK, dir_fd=dirfd)

        func = os.path.islink  # For error reporting.
        try:
            if not os.path.samestat(orig_st, os.fstat(topfd)):
                # Symlinks to directories are forbidden, see GH-46010.
                raise OSError("Cannot call rmtree on a symbolic link")
            stack.append((os.rmdir, dirfd, path, orig_entry))
        finally:
            stack.append((os.close, topfd, path, orig_entry))

        func = os.scandir  # For error reporting.
        with os.scandir(topfd) as scandir_it:
            entries = list(scandir_it)
        for entry in entries:
            fullname = os.path.join(path, entry.name)
            try:
                if entry.is_dir(follow_symlinks=False):
                    # Traverse into sub-directory.
                    stack.append((os.lstat, topfd, fullname, entry))
                    continue
            except FileNotFoundError:
                continue
            except OSError:
                pass
            try:
                os.unlink(entry.name, dir_fd=topfd)
            except FileNotFoundError:
                continue
            except OSError as err:
                onexc(os.unlink, fullname, err)
    except FileNotFoundError as err:
        if orig_entry is None or func is os.close:
            err.filename = path
            onexc(func, path, err)
    except OSError as err:
        err.filename = path
        onexc(func, path, err)