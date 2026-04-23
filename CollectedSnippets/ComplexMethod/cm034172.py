def _load_dependencies(self, attr, ds):
        """
        This is a helper loading function for the dependencies list,
        which returns a list of RoleInclude objects
        """

        roles = []
        if ds:
            if not isinstance(ds, list):
                raise AnsibleParserError("Expected role dependencies to be a list.", obj=self._ds)

            for role_def in ds:
                # FIXME: consolidate with ansible-galaxy to keep this in sync
                if isinstance(role_def, str) or 'role' in role_def or 'name' in role_def:
                    roles.append(role_def)
                    continue
                try:
                    # role_def is new style: { src: 'galaxy.role,version,name', other_vars: "here" }
                    def_parsed = RoleRequirement.role_yaml_parse(role_def)
                    if def_parsed.get('name'):
                        role_def['name'] = def_parsed['name']
                    roles.append(role_def)
                except AnsibleError as ex:
                    raise AnsibleParserError("Error parsing role dependencies.", obj=role_def) from ex

        current_role_path = None
        collection_search_list = None

        if self._owner:
            current_role_path = os.path.dirname(self._owner._role_path)

            # if the calling role has a collections search path defined, consult it
            collection_search_list = self._owner.collections[:] or []

            # if the calling role is a collection role, ensure that its containing collection is searched first
            owner_collection = self._owner._role_collection
            if owner_collection:
                collection_search_list = [c for c in collection_search_list if c != owner_collection]
                collection_search_list.insert(0, owner_collection)
            # ensure fallback role search works
            if 'ansible.legacy' not in collection_search_list:
                collection_search_list.append('ansible.legacy')

        try:
            return load_list_of_roles(roles, play=self._owner._play, current_role_path=current_role_path,
                                      variable_manager=self._variable_manager, loader=self._loader,
                                      collection_search_list=collection_search_list)
        except AssertionError as ex:
            raise AnsibleParserError("A malformed list of role dependencies was encountered.", obj=self._ds) from ex