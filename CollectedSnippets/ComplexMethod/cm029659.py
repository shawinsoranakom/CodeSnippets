def _getfinalpathname_nonstrict(path, ignored_error=OSError):
        # These error codes indicate that we should stop resolving the path
        # and return the value we currently have.
        # 1: ERROR_INVALID_FUNCTION
        # 2: ERROR_FILE_NOT_FOUND
        # 3: ERROR_DIRECTORY_NOT_FOUND
        # 5: ERROR_ACCESS_DENIED
        # 21: ERROR_NOT_READY (implies drive with no media)
        # 32: ERROR_SHARING_VIOLATION (probably an NTFS paging file)
        # 50: ERROR_NOT_SUPPORTED
        # 53: ERROR_BAD_NETPATH
        # 65: ERROR_NETWORK_ACCESS_DENIED
        # 67: ERROR_BAD_NET_NAME (implies remote server unavailable)
        # 87: ERROR_INVALID_PARAMETER
        # 123: ERROR_INVALID_NAME
        # 161: ERROR_BAD_PATHNAME
        # 1005: ERROR_UNRECOGNIZED_VOLUME
        # 1920: ERROR_CANT_ACCESS_FILE
        # 1921: ERROR_CANT_RESOLVE_FILENAME (implies unfollowable symlink)
        allowed_winerror = 1, 2, 3, 5, 21, 32, 50, 53, 65, 67, 87, 123, 161, 1005, 1920, 1921

        # Non-strict algorithm is to find as much of the target directory
        # as we can and join the rest.
        tail = path[:0]
        while path:
            try:
                path = _getfinalpathname(path)
                return join(path, tail) if tail else path
            except ignored_error as ex:
                if ex.winerror not in allowed_winerror:
                    raise
                try:
                    # The OS could not resolve this path fully, so we attempt
                    # to follow the link ourselves. If we succeed, join the tail
                    # and return.
                    new_path = _readlink_deep(path,
                                              ignored_error=ignored_error)
                    if new_path != path:
                        return join(new_path, tail) if tail else new_path
                except ignored_error:
                    # If we fail to readlink(), let's keep traversing
                    pass
                # If we get these errors, try to get the real name of the file without accessing it.
                if ex.winerror in (1, 5, 32, 50, 87, 1920, 1921):
                    try:
                        name = _findfirstfile(path)
                        path, _ = split(path)
                    except ignored_error:
                        path, name = split(path)
                else:
                    path, name = split(path)
                if path and not name:
                    return path + tail
                tail = join(name, tail) if tail else name
        return tail