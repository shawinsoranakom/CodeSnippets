def _return_formatted(self, kwargs):
        _skip_stackwalk = True

        self.add_path_info(kwargs)

        if _PARSED_MODULE_ARGS.get('_ansible_inject_invocation', False):
            if 'invocation' not in kwargs:
                kwargs['invocation'] = {'module_args': self.params}
        else:
            kwargs.pop('invocation', None)

        if 'warnings' in kwargs:
            self.deprecate(  # pylint: disable=ansible-deprecated-unnecessary-collection-name
                msg='Passing `warnings` to `exit_json` or `fail_json` is deprecated.',
                version='2.23',
                help_text='Use `AnsibleModule.warn` instead.',
                deprecator=_deprecator.ANSIBLE_CORE_DEPRECATOR,
            )

            if isinstance(kwargs['warnings'], list):
                for w in kwargs['warnings']:
                    self.warn(w)
            else:
                self.warn(kwargs['warnings'])

        warnings = get_warnings()
        if warnings:
            kwargs['warnings'] = warnings

        if 'deprecations' in kwargs:
            self.deprecate(  # pylint: disable=ansible-deprecated-unnecessary-collection-name
                msg='Passing `deprecations` to `exit_json` or `fail_json` is deprecated.',
                version='2.23',
                help_text='Use `AnsibleModule.deprecate` instead.',
                deprecator=_deprecator.ANSIBLE_CORE_DEPRECATOR,
            )

            if isinstance(kwargs['deprecations'], list):
                for d in kwargs['deprecations']:
                    if isinstance(d, (KeysView, Sequence)) and len(d) == 2:
                        self.deprecate(  # pylint: disable=ansible-deprecated-unnecessary-collection-name,ansible-invalid-deprecated-version
                            msg=d[0],
                            version=d[1],
                            deprecator=_deprecator.get_best_deprecator(),
                        )
                    elif isinstance(d, Mapping):
                        self.deprecate(  # pylint: disable=ansible-deprecated-date-not-permitted,ansible-deprecated-unnecessary-collection-name
                            msg=d['msg'],
                            version=d.get('version'),
                            date=d.get('date'),
                            deprecator=_deprecator.get_best_deprecator(collection_name=d.get('collection_name')),
                        )
                    else:
                        self.deprecate(  # pylint: disable=ansible-deprecated-unnecessary-collection-name,ansible-deprecated-no-version
                            msg=d,
                            deprecator=_deprecator.get_best_deprecator(),
                        )
            else:
                self.deprecate(  # pylint: disable=ansible-deprecated-unnecessary-collection-name,ansible-deprecated-no-version
                    msg=kwargs['deprecations'],
                    deprecator=_deprecator.get_best_deprecator(),
                )

        deprecations = get_deprecations()
        if deprecations:
            kwargs['deprecations'] = deprecations

        # preserve bools/none from no_log
        preserved = {k: v for k, v in kwargs.items() if v is None or isinstance(v, bool)}

        # strip no_log collisions
        kwargs = remove_values(kwargs, self.no_log_values)

        # graft preserved values back on
        kwargs.update(preserved)

        self._record_module_result(kwargs)