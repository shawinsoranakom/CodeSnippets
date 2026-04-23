def __init__(self, paths=None, scan_sys_paths=True, internal_collections=None):
        # TODO: accept metadata loader override
        self._ansible_pkg_path = _to_text(os.path.dirname(_to_bytes(sys.modules['ansible'].__file__)))

        if isinstance(paths, str):
            paths = [paths]
        elif paths is None:
            paths = []

        # expand any placeholders in configured paths
        paths = [os.path.expanduser(_to_text(p)) for p in paths]

        # add syspaths if needed
        if scan_sys_paths:
            paths.extend(sys.path)

        good_paths = []
        # expand any placeholders in configured paths
        for p in paths:

            # ensure we always have ansible_collections
            if os.path.basename(p) == 'ansible_collections':
                p = os.path.dirname(p)

            if p not in good_paths and os.path.isdir(_to_bytes(os.path.join(p, 'ansible_collections'))):
                good_paths.append(p)

        self._internal_collections = internal_collections
        self._n_configured_paths = good_paths
        self._n_cached_collection_paths = None
        self._n_cached_collection_qualified_paths = None

        self._n_playbook_paths = []