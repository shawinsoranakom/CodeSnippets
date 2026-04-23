def _onexc(fn, path, exc):
            assert fn in (os.rmdir, os.unlink)
            if not isinstance(exc, PermissionError):
                raise
            # Make the parent and the children writeable.
            for p, mode in zip(paths, old_modes):
                os.chmod(p, mode)
            # Remove other dirs except one.
            keep = next(p for p in dirs if p != path)
            for p in dirs:
                if p != keep:
                    os.rmdir(p)
            # Remove other files except one.
            keep = next(p for p in files if p != path)
            for p in files:
                if p != keep:
                    os.unlink(p)