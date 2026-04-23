def _find_all_collection_roles(self, name_filters=None, collection_filter=None):
        """Find all collection roles with an argument spec file.

        Note that argument specs do not actually need to exist within the spec file.

        :param name_filters: A tuple of one or more role names used to filter the results. These
            might be fully qualified with the collection name (e.g., community.general.roleA)
            or not (e.g., roleA).

        :param collection_filter: A list of strings containing the FQCN of a collection which will
            be used to limit results. This filter will take precedence over the name_filters.

        :returns: A set of tuples consisting of: role name, collection name, collection path
        """
        found = set()
        b_colldirs = list_collection_dirs(coll_filter=collection_filter)
        for b_path in b_colldirs:
            path = to_text(b_path, errors='surrogate_or_strict')
            if not (collname := _get_collection_name_from_path(b_path)):
                display.debug(f'Skipping invalid path {b_path!r}')
                continue

            roles_dir = os.path.join(path, 'roles')
            if os.path.exists(roles_dir):
                for entry in os.listdir(roles_dir):

                    # Check all potential spec files
                    for specfile in self.ROLE_ARGSPEC_FILES:
                        full_path = os.path.join(roles_dir, entry, 'meta', specfile)
                        if os.path.exists(full_path):
                            if name_filters is None:
                                found.add((entry, collname, path))
                            else:
                                # Name filters might contain a collection FQCN or not.
                                for fqcn in name_filters:
                                    if len(fqcn.split('.')) == 3:
                                        (ns, col, role) = fqcn.split('.')
                                        if '.'.join([ns, col]) == collname and entry == role:
                                            found.add((entry, collname, path))
                                    elif fqcn == entry:
                                        found.add((entry, collname, path))
                            break
        return found