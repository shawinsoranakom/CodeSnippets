def load_data(self, ds, variable_manager=None, loader=None, basedir=None):
        """
        Overrides the base load_data(), as we're actually going to return a new
        Playbook() object rather than a PlaybookInclude object
        """

        # import here to avoid a dependency loop
        from ansible.playbook import Playbook
        from ansible.playbook.play import Play

        # first, we use the original parent method to correctly load the object
        # via the load_data/preprocess_data system we normally use for other
        # playbook objects
        new_obj = super(PlaybookInclude, self).load_data(ds, variable_manager, loader)

        all_vars = self.vars.copy()

        if variable_manager:
            all_vars |= variable_manager.get_vars()

        templar = TemplateEngine(loader=loader, variables=all_vars)

        new_obj.post_validate(templar)

        # then we use the object to load a Playbook
        pb = Playbook(loader=loader)

        file_name = new_obj.import_playbook

        # check for FQCN
        resource = _get_collection_playbook_path(file_name)

        if resource is not None:
            playbook = resource[1]
            playbook_collection = resource[2]
        else:
            # not FQCN try path
            playbook = file_name
            if not os.path.isabs(playbook):
                playbook = os.path.join(basedir, playbook)

            # might still be collection playbook
            playbook_collection = _get_collection_name_from_path(playbook)

        if playbook_collection:
            # it is a collection playbook, setup default collections
            AnsibleCollectionConfig.default_collection = playbook_collection
        else:
            # it is NOT a collection playbook, setup adjacent paths
            AnsibleCollectionConfig.playbook_paths.append(os.path.dirname(os.path.abspath(to_bytes(playbook, errors='surrogate_or_strict'))))
            # broken, see: https://github.com/ansible/ansible/issues/85357

        pb._load_playbook_data(file_name=playbook, variable_manager=variable_manager, vars=self.vars.copy())

        # finally, update each loaded playbook entry with any variables specified
        # on the included playbook and/or any tags which may have been set
        for entry in pb._entries:

            # conditional includes on a playbook need a marker to skip gathering
            if new_obj.when and isinstance(entry, Play):
                entry._included_conditional = new_obj.when[:]

            temp_vars = entry.vars | new_obj.vars
            param_tags = temp_vars.pop('tags', None)
            if param_tags is not None:
                entry.tags.extend(param_tags.split(','))
            entry.vars = temp_vars
            entry.tags = list(set(entry.tags).union(new_obj.tags))
            if entry._included_path is None:
                entry._included_path = os.path.dirname(playbook)

            # Check to see if we need to forward the conditionals on to the included
            # plays. If so, we can take a shortcut here and simply prepend them to
            # those attached to each block (if any)
            if new_obj.when:
                for task_block in (entry.pre_tasks + entry.roles + entry.tasks + entry.post_tasks):
                    task_block._when = new_obj.when[:] + task_block.when[:]

        return pb