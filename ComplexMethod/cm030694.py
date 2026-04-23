def _del_pkg(self, top):
        for entry in list(sys.modules):
            if entry.startswith("__runpy_pkg__"):
                del sys.modules[entry]
        if verbose > 1: print("  Removed sys.modules entries")
        del sys.path[0]
        if verbose > 1: print("  Removed sys.path entry")
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError as ex:
                    if verbose > 1: print(ex) # Persist with cleaning up
            for name in dirs:
                fullname = os.path.join(root, name)
                try:
                    os.rmdir(fullname)
                except OSError as ex:
                    if verbose > 1: print(ex) # Persist with cleaning up
        try:
            os.rmdir(top)
            if verbose > 1: print("  Removed package tree")
        except OSError as ex:
            if verbose > 1: print(ex)