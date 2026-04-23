def get_vars(
        self,
        play: Play | None = None,
        host: Host | None = None,
        task: Task | None = None,
        include_hostvars: bool = True,
        use_cache: bool = True,
        _hosts: list[str] | None = None,
        _hosts_all: list[str] | None = None,
        stage: str = 'task',
    ) -> dict[str, t.Any]:
        """
        Returns the variables, with optional "context" given via the parameters
        for the play, host, and task (which could possibly result in different
        sets of variables being returned due to the additional context).

        The order of precedence is:
        - play->roles->get_default_vars (if there is a play context)
        - group_vars_files[host] (if there is a host context)
        - host->get_vars (if there is a host context)
        - fact_cache[host] (if there is a host context)
        - play vars (if there is a play context)
        - play vars_files (if there's no host context, ignore
          file names that cannot be templated)
        - task->get_vars (if there is a task context)
        - vars_cache[host] (if there is a host context)
        - extra vars

        ``_hosts`` and ``_hosts_all`` should be considered private args, with only internal trusted callers relying
        on the functionality they provide. These arguments may be removed at a later date without a deprecation
        period and without warning.
        """

        display.debug("in VariableManager get_vars()")

        all_vars: dict[str, t.Any] = dict()
        magic_variables = self._get_magic_variables(
            play=play,
            host=host,
            task=task,
            include_hostvars=include_hostvars,
            _hosts=_hosts,
            _hosts_all=_hosts_all,
        )

        def _combine_and_track(data, new_data, source):
            # FIXME: this no longer does any tracking, only a slight optimization for empty new_data
            if new_data == {}:
                return data

            return combine_vars(data, new_data)

        # default for all cases
        basedirs = []
        if self.safe_basedir:  # avoid adhoc/console loading cwd
            basedirs = [self._loader.get_basedir()]

        if play:
            # get role defaults (lowest precedence)
            for role in play.roles:
                if role.public:
                    all_vars = _combine_and_track(all_vars, role.get_default_vars(), "role '%s' defaults" % role.name)

        if task:
            # set basedirs
            if C.PLAYBOOK_VARS_ROOT == 'all':  # should be default
                basedirs = task.get_search_path()
            elif C.PLAYBOOK_VARS_ROOT in ('bottom', 'playbook_dir'):  # only option in 2.4.0
                basedirs = [task.get_search_path()[0]]
            elif C.PLAYBOOK_VARS_ROOT != 'top':
                # preserves default basedirs, only option pre 2.3
                raise AnsibleError('Unknown playbook vars logic: %s' % C.PLAYBOOK_VARS_ROOT)

            # if we have a task in this context, and that task has a role, make
            # sure it sees its defaults above any other roles, as we previously
            # (v1) made sure each task had a copy of its roles default vars
            # TODO: investigate why we need play or include_role check?
            if task._role is not None and (play or task.action in C._ACTION_INCLUDE_ROLE):
                all_vars = _combine_and_track(all_vars, task._role.get_default_vars(dep_chain=task.get_dep_chain()), "role '%s' defaults" % task._role.name)

        if host:
            # THE 'all' group and the rest of groups for a host, used below
            all_group = self._inventory.groups.get('all')
            host_groups = sort_groups([g for g in host.get_groups() if g.name != 'all'])

            # internal functions that actually do the work
            def _plugins_inventory(entities):
                """ merges all entities by inventory source """
                return get_vars_from_inventory_sources(self._loader, self._inventory._sources, entities, stage)

            def _plugins_play(entities):
                """ merges all entities adjacent to play """
                data = {}
                for path in basedirs:
                    data = _combine_and_track(data, get_vars_from_path(self._loader, path, entities, stage), "path '%s'" % path)
                return data

            # configurable functions that are sortable via config, remember to add to _ALLOWED if expanding this list
            def all_inventory():
                return all_group.get_vars()

            def all_plugins_inventory():
                return _plugins_inventory([all_group])

            def all_plugins_play():
                return _plugins_play([all_group])

            def groups_inventory():
                """ gets group vars from inventory """
                return get_group_vars(host_groups)

            def groups_plugins_inventory():
                """ gets plugin sources from inventory for groups """
                return _plugins_inventory(host_groups)

            def groups_plugins_play():
                """ gets plugin sources from play for groups """
                return _plugins_play(host_groups)

            def plugins_by_groups():
                """
                    merges all plugin sources by group,
                    This should be used instead, NOT in combination with the other groups_plugins* functions
                """
                data = {}
                for group in host_groups:
                    data[group] = _combine_and_track(data[group], _plugins_inventory(group), "inventory group_vars for '%s'" % group)
                    data[group] = _combine_and_track(data[group], _plugins_play(group), "playbook group_vars for '%s'" % group)
                return data

            # Merge groups as per precedence config
            # only allow to call the functions we want exposed
            for entry in C.VARIABLE_PRECEDENCE:
                if entry in self._ALLOWED:
                    display.debug('Calling %s to load vars for %s' % (entry, host.name))
                    all_vars = _combine_and_track(all_vars, locals()[entry](), "group vars, precedence entry '%s'" % entry)
                else:
                    display.warning('Ignoring unknown variable precedence entry: %s' % (entry))

            # host vars, from inventory, inventory adjacent and play adjacent via plugins
            all_vars = _combine_and_track(all_vars, host.get_vars(), "host vars for '%s'" % host)
            all_vars = _combine_and_track(all_vars, _plugins_inventory([host]), "inventory host_vars for '%s'" % host)
            all_vars = _combine_and_track(all_vars, _plugins_play([host]), "playbook host_vars for '%s'" % host)

            # finally, the facts caches for this host, if they exist
            try:
                try:
                    facts = self._fact_cache.get(host.name)
                except KeyError:
                    facts = {}

                all_vars |= namespace_facts(facts)

                # push facts to main namespace
                if _INJECT_FACTS:
                    clean_top = _clean_and_deprecate_top_level_facts(facts)
                    all_vars = _combine_and_track(all_vars, clean_top, "facts")
                else:
                    # always 'promote' ansible_local, even if empty
                    all_vars = _combine_and_track(all_vars, {'ansible_local': facts.get('ansible_local', {})}, "facts")
            except KeyError:
                pass

        if play:
            all_vars = _combine_and_track(all_vars, play.get_vars(), "play vars")

            vars_files = play.get_vars_files()

            for vars_file_item in vars_files:
                # create a set of temporary vars here, which incorporate the extra
                # and magic vars so we can properly template the vars_files entries
                # NOTE: this makes them depend on host vars/facts so things like
                #       ansible_facts['os_distribution'] can be used, ala include_vars.
                #       Consider DEPRECATING this in the future, since we have include_vars ...
                temp_vars = combine_vars(all_vars, self._extra_vars)
                temp_vars = combine_vars(temp_vars, magic_variables)
                templar = TemplateEngine(loader=self._loader, variables=temp_vars)

                # we assume each item in the list is itself a list, as we
                # support "conditional includes" for vars_files, which mimics
                # the with_first_found mechanism.
                vars_file_list = vars_file_item
                if not isinstance(vars_file_list, list):
                    vars_file_list = [vars_file_list]

                # now we iterate through the (potential) files, and break out
                # as soon as we read one from the list. If none are found, we
                # raise an error, which is silently ignored at this point.
                try:
                    for vars_file in vars_file_list:
                        vars_file = templar.template(vars_file)
                        if not (isinstance(vars_file, str)):
                            raise AnsibleParserError(
                                message=f"Invalid `vars_files` value of type {native_type_name(vars_file)!r}.",
                                obj=vars_file,
                                help_text="A `vars_files` value should either be a string or list of strings.",
                            )
                        try:
                            play_search_stack = play.get_search_path()
                            found_file = self._loader.path_dwim_relative_stack(play_search_stack, 'vars', vars_file)
                            data = preprocess_vars(self._loader.load_from_file(found_file, unsafe=True, cache='vaulted', trusted_as_template=True))
                            if data is not None:
                                for item in data:
                                    all_vars = _combine_and_track(all_vars, item, f"play vars_files from {vars_file!r}")
                            display.vvv(f"Read `vars_file` {found_file!r}.")
                            break
                        except AnsibleFileNotFound:
                            # we continue on loader failures
                            continue
                        except (AnsibleParserError, AnsibleUndefinedVariable):
                            raise
                        except AnsibleError as e:
                            raise AnsibleError(f"Invalid vars_files file {found_file!r}.") from e

                except AnsibleUndefinedVariable as ex:
                    if host is not None:
                        try:
                            facts = self._fact_cache.get(host.name)
                        except KeyError:
                            pass
                        else:
                            if facts.get('module_setup') and task is not None:
                                raise AnsibleUndefinedVariable("an undefined variable was found when attempting to template the vars_files item '%s'"
                                                               % vars_file_item, obj=vars_file_item) from ex

                    display.warning("skipping vars_files item due to an undefined variable", obj=vars_file_item)
                    continue

            # We now merge in all exported vars from all roles in the play (very high precedence)
            for role in play.roles:
                if role.public:
                    all_vars = _combine_and_track(all_vars, role.get_vars(include_params=False, only_exports=True), "role '%s' exported vars" % role.name)

        # next, we merge in the vars from the role, which will specifically
        # follow the role dependency chain, and then we merge in the tasks
        # vars (which will look at parent blocks/task includes)
        if task:
            if task._role:
                all_vars = _combine_and_track(all_vars, task._role.get_vars(task.get_dep_chain(), include_params=False, only_exports=False),
                                              "role '%s' all vars" % task._role.name)
            all_vars = _combine_and_track(all_vars, task.get_vars(), "task vars")

        # next, we merge in the vars cache (include vars) and nonpersistent
        # facts cache (set_fact/register), in that order
        if host:
            # include_vars non-persistent cache
            all_vars = _combine_and_track(all_vars, self._vars_cache.get(host.get_name(), dict()), "include_vars")
            # fact non-persistent cache (this also includes registered variables and host variables set at runtime)
            all_vars = _combine_and_track(all_vars, self._nonpersistent_fact_cache.get(host.name, dict()), "set_fact")

        # next, we merge in role params and task include params
        if task:
            # special case for include tasks, where the include params
            # may be specified in the vars field for the task, which should
            # have higher precedence than the vars/np facts above
            if task._role:
                all_vars = _combine_and_track(all_vars, task._role.get_role_params(task.get_dep_chain()), "role params")
            all_vars = _combine_and_track(all_vars, task.get_include_params(), "include params")

        # extra vars
        all_vars = _combine_and_track(all_vars, self._extra_vars, "extra vars")

        # before we add 'reserved vars', check we didn't add any reserved vars
        warn_if_reserved(all_vars)

        # magic variables
        all_vars = _combine_and_track(all_vars, magic_variables, "magic vars")

        # special case for the 'environment' magic variable, as someone
        # may have set it as a variable and we don't want to stomp on it
        if task:
            all_vars['environment'] = task.environment

        # 'vars' magic var
        if task or play:
            all_vars['vars'] = _DEPRECATE_VARS.tag({})
            for k, v in all_vars.items():
                # has to be copy, otherwise recursive ref
                all_vars['vars'][k] = _DEPRECATE_VARS.tag(v)

        display.debug("done with get_vars()")
        return all_vars