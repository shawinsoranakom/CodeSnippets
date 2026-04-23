def _get_magic_variables(self, play, host, task, include_hostvars, _hosts=None, _hosts_all=None):
        """
        Returns a dictionary of so-called "magic" variables in Ansible,
        which are special variables we set internally for use.
        """

        variables = {}
        variables['playbook_dir'] = self._loader.get_basedir()
        variables['ansible_playbook_python'] = sys.executable
        variables['ansible_config_file'] = C.CONFIG_FILE

        if play:
            # using role_cache as play.roles only has 'public' roles for vars exporting
            dependency_role_names = list({d.get_name() for r in play.roles for d in r.get_all_dependencies()})
            play_role_names = [r.get_name() for r in play.roles]

            # ansible_role_names includes all role names, dependent or directly referenced by the play
            variables['ansible_role_names'] = list(set(dependency_role_names + play_role_names))
            # ansible_play_role_names includes the names of all roles directly referenced by this play
            # roles that are implicitly referenced via dependencies are not listed.
            variables['ansible_play_role_names'] = play_role_names
            # ansible_dependent_role_names includes the names of all roles that are referenced via dependencies
            # dependencies that are also explicitly named as roles are included in this list
            variables['ansible_dependent_role_names'] = dependency_role_names

            # TODO: data tagging!!! DEPRECATED: role_names should be deprecated in favor of ansible_ prefixed ones
            variables['role_names'] = variables['ansible_play_role_names']

            variables['ansible_play_name'] = play.get_name()

        if task:
            if task._role:
                variables['role_name'] = task._role.get_name(include_role_fqcn=False)
                variables['role_path'] = task._role._role_path
                variables['role_uuid'] = str(task._role._uuid)
                variables['ansible_collection_name'] = task._role._role_collection
                variables['ansible_role_name'] = task._role.get_name()

        if self._inventory is not None:
            variables['groups'] = self._inventory.get_groups_dict()
            if play:
                # add the list of hosts in the play, as adjusted for limit/filters
                if not _hosts_all:
                    if not play.finalized and TemplateEngine().is_template(play.hosts):
                        pattern = 'all'
                    else:
                        pattern = play.hosts or 'all'

                    _hosts_all = [h.name for h in self._inventory.get_hosts(pattern=pattern, ignore_restrictions=True)]
                if not _hosts:
                    _hosts = [h.name for h in self._inventory.get_hosts()]

                variables['ansible_play_hosts_all'] = _hosts_all[:]
                variables['ansible_play_hosts'] = [x for x in variables['ansible_play_hosts_all'] if x not in play._removed_hosts]
                variables['ansible_play_batch'] = [x for x in _hosts if x not in play._removed_hosts]

                # use a static tag instead of `deprecate_value` to avoid stackwalk in a hot code path
                variables['play_hosts'] = self._PLAY_HOSTS_DEPRECATED_TAG.tag(variables['ansible_play_batch'])

        # Set options vars
        for option, option_value in self._options_vars.items():
            variables[option] = option_value

        if self._hostvars is not None and include_hostvars:
            variables['hostvars'] = self._hostvars

        return variables