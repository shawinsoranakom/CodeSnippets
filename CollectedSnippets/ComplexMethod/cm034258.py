def _normalize_parameters(self, thing, action=None, additional_args=None):
        """
        arguments can be fuzzy.  Deal with all the forms.
        """

        # final args are the ones we'll eventually return, so first update
        # them with any additional args specified, which have lower priority
        # than those which may be parsed/normalized next
        final_args = dict()

        if additional_args is not Sentinel:
            if isinstance(additional_args, str) and _jinja_bits.is_possibly_all_template(additional_args):
                final_args['_variable_params'] = additional_args
            elif isinstance(additional_args, dict):
                final_args.update(additional_args)
            elif additional_args is None:
                Display().deprecated(
                    msg="Ignoring empty task `args` keyword.",
                    version="2.23",
                    help_text='A mapping or template which resolves to a mapping is required.',
                    obj=self._task_ds,
                )
            else:
                raise AnsibleParserError(
                    message='The value of the task `args` keyword is invalid.',
                    help_text='A mapping or template which resolves to a mapping is required.',
                    obj=additional_args,
                )

        # how we normalize depends if we figured out what the module name is
        # yet.  If we have already figured it out, it's a 'new style' invocation.
        # otherwise, it's not

        if action is not None:
            args = self._normalize_new_style_args(thing, action, additional_args)
        else:
            (action, args) = self._normalize_old_style_args(thing)

            # this can occasionally happen, simplify
            if args and 'args' in args:
                tmp_args = args.pop('args')
                if isinstance(tmp_args, str):
                    tmp_args = parse_kv(tmp_args)
                args.update(tmp_args)

        # only internal variables can start with an underscore, so
        # we don't allow users to set them directly in arguments
        if args and action not in FREEFORM_ACTIONS:
            for arg in args:
                arg = to_text(arg)
                if arg.startswith('_ansible_'):
                    err_msg = (
                        f"Invalid parameter specified beginning with keyword '_ansible_' for action '{action !s}': '{arg !s}'. "
                        "The prefix '_ansible_' is reserved for internal use only."
                    )
                    raise AnsibleError(err_msg)

        # finally, update the args we're going to return with the ones
        # which were normalized above
        if args:
            final_args.update(args)

        return (action, final_args)