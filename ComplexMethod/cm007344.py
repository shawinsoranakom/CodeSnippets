def compat_expanduser(path):
            """Expand ~ and ~user constructs.

            If user or $HOME is unknown, do nothing."""
            if path[:1] != '~':
                return path
            i, n = 1, len(path)
            while i < n and path[i] not in '/\\':
                i = i + 1

            if 'HOME' in os.environ:
                userhome = compat_getenv('HOME')
            elif 'USERPROFILE' in os.environ:
                userhome = compat_getenv('USERPROFILE')
            elif 'HOMEPATH' not in os.environ:
                return path
            else:
                try:
                    drive = compat_getenv('HOMEDRIVE')
                except KeyError:
                    drive = ''
                userhome = os.path.join(drive, compat_getenv('HOMEPATH'))

            if i != 1:  # ~user
                userhome = os.path.join(os.path.dirname(userhome), path[1:i])

            return userhome + path[i:]