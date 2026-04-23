def _resolve_group(self, fq_group_name, mandatory=True):
        if not AnsibleCollectionRef.is_valid_fqcr(fq_group_name):
            collection_name = 'ansible.builtin'
            fq_group_name = collection_name + '.' + fq_group_name
        else:
            collection_name = '.'.join(fq_group_name.split('.')[0:2])

        # Check if the group has already been resolved and cached
        if fq_group_name in self.play._group_actions:
            return fq_group_name, self.play._group_actions[fq_group_name]

        try:
            action_groups = _get_collection_metadata(collection_name).get('action_groups', {})
        except ValueError:
            if not mandatory:
                display.vvvvv("Error loading module_defaults: could not resolve the module_defaults group %s" % fq_group_name)
                return fq_group_name, []

            raise AnsibleParserError("Error loading module_defaults: could not resolve the module_defaults group %s" % fq_group_name)

        # The collection may or may not use the fully qualified name
        # Don't fail if the group doesn't exist in the collection
        resource_name = fq_group_name.split(collection_name + '.')[-1]
        action_group = action_groups.get(
            fq_group_name,
            action_groups.get(resource_name)
        )
        if action_group is None:
            if not mandatory:
                display.vvvvv("Error loading module_defaults: could not resolve the module_defaults group %s" % fq_group_name)
                return fq_group_name, []
            raise AnsibleParserError("Error loading module_defaults: could not resolve the module_defaults group %s" % fq_group_name)

        resolved_actions = []
        include_groups = []

        found_group_metadata = False
        for action in action_group:
            # Everything should be a string except the metadata entry
            if not isinstance(action, str):
                _validate_action_group_metadata(action, found_group_metadata, fq_group_name)

                if isinstance(action['metadata'], dict):
                    found_group_metadata = True

                    include_groups = action['metadata'].get('extend_group', [])
                    if isinstance(include_groups, str):
                        include_groups = [include_groups]
                    if not isinstance(include_groups, list):
                        # Bad entries may be a warning above, but prevent tracebacks by setting it back to the acceptable type.
                        include_groups = []
                continue

            # The collection may or may not use the fully qualified name.
            # If not, it's part of the current collection.
            if not AnsibleCollectionRef.is_valid_fqcr(action):
                action = collection_name + '.' + action
            resolved_action = self._resolve_action(action, mandatory=False)
            if resolved_action:
                resolved_actions.append(resolved_action)

        for action in resolved_actions:
            if action not in self.play._action_groups:
                self.play._action_groups[action] = []
            self.play._action_groups[action].append(fq_group_name)

        self.play._group_actions[fq_group_name] = resolved_actions

        # Resolve extended groups last, after caching the group in case they recursively refer to each other
        for include_group in include_groups:
            if not AnsibleCollectionRef.is_valid_fqcr(include_group):
                include_group = collection_name + '.' + include_group

            dummy, group_actions = self._resolve_group(include_group, mandatory=False)

            for action in group_actions:
                if action not in self.play._action_groups:
                    self.play._action_groups[action] = []
                self.play._action_groups[action].append(fq_group_name)

            self.play._group_actions[fq_group_name].extend(group_actions)
            resolved_actions.extend(group_actions)

        return fq_group_name, resolved_actions