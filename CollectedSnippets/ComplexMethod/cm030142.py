def _fwalk(stack, isbytes, topdown, onerror, follow_symlinks):
        # Note: This uses O(depth of the directory tree) file descriptors: if
        # necessary, it can be adapted to only require O(1) FDs, see issue
        # #13734.

        action, value = stack.pop()
        if action == _fwalk_close:
            close(value)
            return
        elif action == _fwalk_yield:
            yield value
            return
        assert action == _fwalk_walk
        isroot, dirfd, toppath, topname, entry = value
        try:
            if not follow_symlinks:
                # Note: To guard against symlink races, we use the standard
                # lstat()/open()/fstat() trick.
                if entry is None:
                    orig_st = stat(topname, follow_symlinks=False, dir_fd=dirfd)
                else:
                    orig_st = entry.stat(follow_symlinks=False)
            topfd = open(topname, O_RDONLY | O_NONBLOCK, dir_fd=dirfd)
        except OSError as err:
            if isroot:
                raise
            if onerror is not None:
                onerror(err)
            return
        stack.append((_fwalk_close, topfd))
        if not follow_symlinks:
            if isroot and not st.S_ISDIR(orig_st.st_mode):
                return
            if not path.samestat(orig_st, stat(topfd)):
                return

        scandir_it = scandir(topfd)
        dirs = []
        nondirs = []
        entries = None if topdown or follow_symlinks else []
        for entry in scandir_it:
            name = entry.name
            if isbytes:
                name = fsencode(name)
            try:
                if entry.is_dir():
                    dirs.append(name)
                    if entries is not None:
                        entries.append(entry)
                else:
                    nondirs.append(name)
            except OSError:
                try:
                    # Add dangling symlinks, ignore disappeared files
                    if entry.is_symlink():
                        nondirs.append(name)
                except OSError:
                    pass

        if topdown:
            yield toppath, dirs, nondirs, topfd
        else:
            stack.append((_fwalk_yield, (toppath, dirs, nondirs, topfd)))

        toppath = path.join(toppath, toppath[:0])  # Add trailing slash.
        if entries is None:
            stack.extend(
                (_fwalk_walk, (False, topfd, toppath + name, name, None))
                for name in dirs[::-1])
        else:
            stack.extend(
                (_fwalk_walk, (False, topfd, toppath + name, name, entry))
                for name, entry in zip(dirs[::-1], entries[::-1]))