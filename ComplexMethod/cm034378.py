def contentfilter(fsname, pattern, encoding, read_whole_file=False):
    """
    Filter files which contain the given expression
    :arg fsname: Filename to scan for lines matching a pattern
    :arg pattern: Pattern to look for inside of line
    :arg encoding: Encoding of the file to be scanned
    :arg read_whole_file: If true, the whole file is read into memory before the regex is applied against it. Otherwise, the regex is applied line-by-line.
    :rtype: bool
    :returns: True if one of the lines in fsname matches the pattern. Otherwise False
    """
    if pattern is None:
        return True

    prog = re.compile(pattern)

    try:
        with open(fsname, encoding=encoding) as f:
            if read_whole_file:
                return bool(prog.search(f.read()))

            for line in f:
                if prog.match(line):
                    return True

    except LookupError as e:
        raise e
    except UnicodeDecodeError as e:
        if encoding is None:
            # Get the default encoding for the current locale
            # This is the same encoding that the open() function uses by default
            # when no encoding is specified. This value is platform dependent.
            #
            # https://docs.python.org/3/library/functions.html#open
            encoding = f"{locale.getpreferredencoding(False).lower()} (Python default)"
        msg = f'Failed to decode the file {fsname!r} with encoding: {encoding}'
        raise Exception(msg) from e
    except Exception:
        pass

    return False