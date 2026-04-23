def _find_all_normal_roles(self, role_paths, name_filters=None):
        """Find all non-collection roles that have an argument spec file.

        Note that argument specs do not actually need to exist within the spec file.

        :param role_paths: A tuple of one or more role paths. When a role with the same name
            is found in multiple paths, only the first-found role is returned.
        :param name_filters: A tuple of one or more role names used to filter the results.

        :returns: A set of tuples consisting of: role name, full role path
        """
        found = set()
        found_names = set()

        for path in role_paths:
            if not os.path.isdir(path):
                continue

            # Check each subdir for an argument spec file
            for entry in os.listdir(path):
                role_path = os.path.join(path, entry)

                # Check all potential spec files
                for specfile in self.ROLE_ARGSPEC_FILES:
                    full_path = os.path.join(role_path, 'meta', specfile)
                    if os.path.exists(full_path):
                        if name_filters is None or entry in name_filters:
                            # select first-found role
                            if entry not in found_names:
                                found_names.add(entry)
                                # None here stands for 'colleciton', which stand alone roles dont have
                                # makes downstream code simpler by having same structure as collection roles
                                found.add((entry, None, role_path))
                        # only read first existing spec
                        break
        return found