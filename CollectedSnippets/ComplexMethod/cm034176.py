def _load_role_path(self, role_name):
        """
        the 'role', as specified in the ds (or as a bare string), can either
        be a simple name or a full path. If it is a full path, we use the
        basename as the role name, otherwise we take the name as-given and
        append it to the default role path
        """

        # create a templar class to template the dependency names, in
        # case they contain variables
        if self._variable_manager is not None:
            all_vars = self._variable_manager.get_vars(play=self._play)
        else:
            all_vars = dict()

        templar = TemplateEngine(loader=self._loader, variables=all_vars)
        role_name = templar.template(role_name)

        role_tuple = None

        # try to load as a collection-based role first
        if self._collection_list or AnsibleCollectionRef.is_valid_fqcr(role_name):
            role_tuple = _get_collection_role_path(role_name, self._collection_list)

        if role_tuple:
            # we found it, stash collection data and return the name/path tuple
            self._role_collection = role_tuple[2]
            return role_tuple[0:2]

        # We didn't find a collection role, look in defined role paths
        # FUTURE: refactor this to be callable from internal so we can properly order
        # ansible.legacy searches with the collections keyword

        # we always start the search for roles in the base directory of the playbook
        role_search_paths = [
            os.path.join(self._loader.get_basedir(), u'roles'),
        ]

        # also search in the configured roles path
        if C.DEFAULT_ROLES_PATH:
            role_search_paths.extend(C.DEFAULT_ROLES_PATH)

        # next, append the roles basedir, if it was set, so we can
        # search relative to that directory for dependent roles
        if self._role_basedir:
            role_search_paths.append(self._role_basedir)

        # finally as a last resort we look in the current basedir as set
        # in the loader (which should be the playbook dir itself) but without
        # the roles/ dir appended
        role_search_paths.append(self._loader.get_basedir())

        # now iterate through the possible paths and return the first one we find
        for path in role_search_paths:
            path = templar.template(path)
            role_path = unfrackpath(os.path.join(path, role_name))
            if self._loader.path_exists(role_path):
                return (role_name, role_path)

        # if not found elsewhere try to extract path from name
        role_path = unfrackpath(role_name)
        if self._loader.path_exists(role_path):
            role_name = os.path.basename(role_name)
            return (role_name, role_path)

        searches = (self._collection_list or []) + role_search_paths

        raise AnsibleError(f"The role {role_name!r} was not found in: {':'.join(searches)}", obj=self._ds)