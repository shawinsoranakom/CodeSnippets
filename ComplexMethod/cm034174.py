def _load_role_data(self, role_include, parent_role=None):
        self._role_name = role_include.role
        self._role_path = role_include.get_role_path()
        self._role_collection = role_include._role_collection
        self._role_params = role_include.get_role_params()
        self._variable_manager = role_include.get_variable_manager()
        self._loader = role_include.get_loader()

        if parent_role:
            self.add_parent(parent_role)

        # copy over all field attributes from the RoleInclude
        # update self._attr directly, to avoid squashing
        for attr_name in self.fattributes:
            setattr(self, f'_{attr_name}', getattr(role_include, f'_{attr_name}', Sentinel))

        # vars and default vars are regular dictionaries
        self._role_vars = self._load_role_yaml('vars', main=self._from_files.get('vars'), allow_dir=True)
        if self._role_vars is None:
            self._role_vars = {}
        elif not isinstance(self._role_vars, Mapping):
            raise AnsibleParserError("The vars/main.yml file for role '%s' must contain a dictionary of variables" % self._role_name)

        self._default_vars = self._load_role_yaml('defaults', main=self._from_files.get('defaults'), allow_dir=True)
        if self._default_vars is None:
            self._default_vars = {}
        elif not isinstance(self._default_vars, Mapping):
            raise AnsibleParserError("The defaults/main.yml file for role '%s' must contain a dictionary of variables" % self._role_name)

        # load the role's other files, if they exist
        metadata = self._load_role_yaml('meta')
        if metadata:
            self._metadata = RoleMetadata.load(metadata, owner=self, variable_manager=self._variable_manager, loader=self._loader)
            self._dependencies = self._load_dependencies()

        # reset collections list; roles do not inherit collections from parents, just use the defaults
        # FUTURE: use a private config default for this so we can allow it to be overridden later
        self.collections = []

        # configure plugin/collection loading; either prepend the current role's collection or configure legacy plugin loading
        # FIXME: need exception for explicit ansible.legacy?
        if self._role_collection:  # this is a collection-hosted role
            self.collections.insert(0, self._role_collection)
        else:  # this is a legacy role, but set the default collection if there is one
            default_collection = AnsibleCollectionConfig.default_collection
            if default_collection:
                self.collections.insert(0, default_collection)
            # legacy role, ensure all plugin dirs under the role are added to plugin search path
            add_all_plugin_dirs(self._role_path)

        # collections can be specified in metadata for legacy or collection-hosted roles
        if self._metadata.collections:
            self.collections.extend((c for c in self._metadata.collections if c not in self.collections))

        # if any collections were specified, ensure that core or legacy synthetic collections are always included
        if self.collections:
            # default append collection is core for collection-hosted roles, legacy for others
            default_append_collection = 'ansible.builtin' if self._role_collection else 'ansible.legacy'
            if 'ansible.builtin' not in self.collections and 'ansible.legacy' not in self.collections:
                self.collections.append(default_append_collection)

        task_data = self._load_role_yaml('tasks', main=self._from_files.get('tasks'))

        if self._should_validate:
            role_argspecs = self._get_role_argspecs()
            task_data = self._prepend_validation_task(task_data, role_argspecs)

        if task_data:
            try:
                self._task_blocks = load_list_of_blocks(task_data, play=self._play, role=self, loader=self._loader, variable_manager=self._variable_manager)
            except AssertionError as ex:
                raise AnsibleParserError(f"The tasks/main.yml file for role {self._role_name!r} must contain a list of tasks.", obj=task_data) from ex

        handler_data = self._load_role_yaml('handlers', main=self._from_files.get('handlers'))
        if handler_data:
            try:
                self._handler_blocks = load_list_of_blocks(handler_data, play=self._play, role=self, use_handlers=True, loader=self._loader,
                                                           variable_manager=self._variable_manager)
            except AssertionError as ex:
                raise AnsibleParserError(f"The handlers/main.yml file for role {self._role_name!r} must contain a list of tasks.",
                                         obj=handler_data) from ex