def realpath(path, /, *, strict=False):
        path = normpath(path)
        if isinstance(path, bytes):
            prefix = b'\\\\?\\'
            unc_prefix = b'\\\\?\\UNC\\'
            new_unc_prefix = b'\\\\'
            cwd = os.getcwdb()
            # bpo-38081: Special case for realpath(b'nul')
            devnull = b'nul'
            if normcase(path) == devnull:
                return b'\\\\.\\NUL'
        else:
            prefix = '\\\\?\\'
            unc_prefix = '\\\\?\\UNC\\'
            new_unc_prefix = '\\\\'
            cwd = os.getcwd()
            # bpo-38081: Special case for realpath('nul')
            devnull = 'nul'
            if normcase(path) == devnull:
                return '\\\\.\\NUL'
        had_prefix = path.startswith(prefix)

        if strict is ALLOW_MISSING:
            ignored_error = FileNotFoundError
        elif strict is ALL_BUT_LAST:
            ignored_error = FileNotFoundError
        elif strict:
            ignored_error = ()
        else:
            ignored_error = OSError

        if not had_prefix and not isabs(path):
            path = join(cwd, path)
        try:
            path = _getfinalpathname(path)
            initial_winerror = 0
        except ValueError as ex:
            # gh-106242: Raised for embedded null characters
            # In strict modes, we convert into an OSError.
            # Non-strict mode returns the path as-is, since we've already
            # made it absolute.
            if strict:
                raise OSError(str(ex)) from None
            path = normpath(path)
        except ignored_error as ex:
            if strict is ALL_BUT_LAST:
                dirname, basename = split(path)
                if not basename:
                    dirname, basename = split(path)
                if not isdir(dirname):
                    raise
            initial_winerror = ex.winerror
            path = _getfinalpathname_nonstrict(path,
                                               ignored_error=ignored_error)
        # The path returned by _getfinalpathname will always start with \\?\ -
        # strip off that prefix unless it was already provided on the original
        # path.
        if not had_prefix and path.startswith(prefix):
            # For UNC paths, the prefix will actually be \\?\UNC\
            # Handle that case as well.
            if path.startswith(unc_prefix):
                spath = new_unc_prefix + path[len(unc_prefix):]
            else:
                spath = path[len(prefix):]
            # Ensure that the non-prefixed path resolves to the same path
            try:
                if _getfinalpathname(spath) == path:
                    path = spath
            except ValueError:
                # Unexpected, as an invalid path should not have gained a prefix
                # at any point, but we ignore this error just in case.
                pass
            except OSError as ex:
                # If the path does not exist and originally did not exist, then
                # strip the prefix anyway.
                if ex.winerror == initial_winerror:
                    path = spath
        return path