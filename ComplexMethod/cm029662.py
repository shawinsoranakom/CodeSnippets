def normpath(path):
        """Normalize path, eliminating double slashes, etc."""
        path = os.fspath(path)
        if isinstance(path, bytes):
            sep = b'\\'
            altsep = b'/'
            curdir = b'.'
            pardir = b'..'
        else:
            sep = '\\'
            altsep = '/'
            curdir = '.'
            pardir = '..'
        path = path.replace(altsep, sep)
        drive, root, path = splitroot(path)
        prefix = drive + root
        comps = path.split(sep)
        i = 0
        while i < len(comps):
            if not comps[i] or comps[i] == curdir:
                del comps[i]
            elif comps[i] == pardir:
                if i > 0 and comps[i-1] != pardir:
                    del comps[i-1:i+1]
                    i -= 1
                elif i == 0 and root:
                    del comps[i]
                else:
                    i += 1
            else:
                i += 1
        # If the path is now empty, substitute '.'
        if not prefix and not comps:
            comps.append(curdir)
        return prefix + sep.join(comps)