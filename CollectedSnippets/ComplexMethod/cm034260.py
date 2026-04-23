def parse(self, skip_action_validation=False):
        """
        Given a task in one of the supported forms, parses and returns
        returns the action, arguments, and delegate_to values for the
        task, dealing with all sorts of levels of fuzziness.
        """

        action = None
        delegate_to = self._task_ds.get('delegate_to', Sentinel)
        args = dict()

        # This is the standard YAML form for command-type modules. We grab
        # the args and pass them in as additional arguments, which can/will
        # be overwritten via dict updates from the other arg sources below
        additional_args = self._task_ds.get('args', Sentinel)

        # We can have one of action, local_action, or module specified
        # action
        if 'action' in self._task_ds:
            # an old school 'action' statement
            thing = self._task_ds['action']
            action, args = self._normalize_parameters(thing, additional_args=additional_args)

        # local_action
        if 'local_action' in self._task_ds:
            # local_action is similar but also implies a delegate_to
            if action is not None:
                raise AnsibleParserError("action and local_action are mutually exclusive", obj=self._task_ds)
            thing = self._task_ds.get('local_action', '')
            delegate_to = 'localhost'
            action, args = self._normalize_parameters(thing, additional_args=additional_args)

        # module: <stuff> is the more new-style invocation

        # filter out task attributes so we're only querying unrecognized keys as actions/modules
        non_task_ds = dict((k, v) for k, v in self._task_ds.items() if (k not in self._task_attrs) and (not k.startswith('with_')))

        # walk the filtered input dictionary to see if we recognize a module name
        for item, value in non_task_ds.items():
            if item in BUILTIN_TASKS:
                is_action_candidate = True
            elif skip_action_validation:
                is_action_candidate = True
            else:
                try:
                    # DTFIX-FUTURE: extract to a helper method, shared with Task.post_validate_args
                    context = _get_action_context(item, self._collection_list)
                except AnsibleError as e:
                    if e.obj is None:
                        e.obj = self._task_ds
                    raise e

                is_action_candidate = context.resolved and bool(context.redirect_list)
                if is_action_candidate:
                    self._resolved_action = context.resolved_fqcn

            if is_action_candidate:
                # finding more than one module name is a problem
                if action is not None:
                    raise AnsibleParserError("conflicting action statements: %s, %s" % (action, item), obj=self._task_ds)

                action = item
                thing = value
                action, args = self._normalize_parameters(thing, action=action, additional_args=additional_args)

        # if we didn't see any module in the task at all, it's not a task really
        if action is None:
            if non_task_ds:  # there was one non-task action, but we couldn't find it
                bad_action = list(non_task_ds.keys())[0]
                raise AnsibleParserError("couldn't resolve module/action '{0}'. This often indicates a "
                                         "misspelling, missing collection, or incorrect module path.".format(bad_action),
                                         obj=self._task_ds)
            else:
                raise AnsibleParserError("no module/action detected in task.",
                                         obj=self._task_ds)

        return action, args, delegate_to