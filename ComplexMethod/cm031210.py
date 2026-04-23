def _path_join(*path_parts):
        """Replacement for os.path.join()."""
        if not path_parts:
            return ""
        if len(path_parts) == 1:
            return path_parts[0]
        root = ""
        path = []
        for new_root, tail in map(_os._path_splitroot, path_parts):
            if new_root.startswith(path_sep_tuple) or new_root.endswith(path_sep_tuple):
                root = new_root.rstrip(path_separators) or root
                path = [path_sep + tail]
            elif new_root.endswith(':'):
                if root.casefold() != new_root.casefold():
                    # Drive relative paths have to be resolved by the OS, so we reset the
                    # tail but do not add a path_sep prefix.
                    root = new_root
                    path = [tail]
                else:
                    path.append(tail)
            else:
                root = new_root or root
                path.append(tail)
        path = [p.rstrip(path_separators) for p in path if p]
        if len(path) == 1 and not path[0]:
            # Avoid losing the root's trailing separator when joining with nothing
            return root + path_sep
        return root + path_sep.join(path)