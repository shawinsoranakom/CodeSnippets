def _normalize_new_style_args(self, thing, action, additional_args):
        """
        deals with fuzziness in new style module invocations
        accepting key=value pairs and dictionaries, and returns
        a dictionary of arguments

        possible example inputs:
            'echo hi', 'shell'
            {'region': 'xyz'}, 'ec2'
        standardized outputs like:
            { _raw_params: 'echo hi', _uses_shell: True }
        """

        if isinstance(thing, dict):
            # form is like: { xyz: { x: 2, y: 3 } }
            args = thing
        elif isinstance(thing, str):
            # form is like: copy: src=a dest=b
            check_raw = action in FREEFORM_ACTIONS
            args = parse_kv(thing, check_raw=check_raw)
            args_keys = set(args) - {'_raw_params'}

            if args_keys and additional_args is not Sentinel:
                kv_args = ', '.join(repr(arg) for arg in sorted(args_keys))

                Display().deprecated(
                    msg=f"Merging legacy k=v args ({kv_args}) into task args.",
                    help_text="Include all task args in the task `args` mapping.",
                    version="2.23",
                    obj=thing,
                )
        elif isinstance(thing, EncryptedString):
            # k=v parsing intentionally omitted
            args = dict(_raw_params=thing)
        elif thing is None:
            # this can happen with modules which take no params, like ping:
            args = None
        else:
            raise AnsibleParserError("unexpected parameter type in action: %s" % type(thing), obj=self._task_ds)
        return args