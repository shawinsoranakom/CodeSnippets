def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)