def _get_loader(self, fullname, path=None):
        split_name = fullname.split('.')
        toplevel_pkg = split_name[0]
        module_to_find = split_name[-1]
        part_count = len(split_name)

        if toplevel_pkg not in ['ansible', 'ansible_collections']:
            # not interested in anything other than ansible_collections (and limited cases under ansible)
            return None

        # sanity check what we're getting from import, canonicalize path values
        if part_count == 1:
            if path:
                raise ValueError('path should not be specified for top-level packages (trying to find {0})'.format(fullname))
            else:
                # seed the path to the configured collection roots
                path = self._n_collection_paths

        if part_count > 1 and path is None:
            raise ValueError('path must be specified for subpackages (trying to find {0})'.format(fullname))

        if toplevel_pkg == 'ansible':
            # something under the ansible package, delegate to our internal loader in case of redirections
            initialize_loader = _AnsibleInternalRedirectLoader
        elif part_count == 1:
            initialize_loader = _AnsibleCollectionRootPkgLoader
        elif part_count == 2:  # ns pkg eg, ansible_collections, ansible_collections.somens
            initialize_loader = _AnsibleCollectionNSPkgLoader
        elif part_count == 3:  # collection pkg eg, ansible_collections.somens.somecoll
            initialize_loader = _AnsibleCollectionPkgLoader
        else:
            # anything below the collection
            initialize_loader = _AnsibleCollectionLoader

        # NB: actual "find"ing is delegated to the constructors on the various loaders; they'll ImportError if not found
        try:
            return initialize_loader(fullname=fullname, path_list=path)
        except ImportError:
            # TODO: log attempt to load context
            return None