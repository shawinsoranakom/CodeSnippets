def load_extra_vars(loader: DataLoader) -> dict[str, t.Any]:

    if not getattr(load_extra_vars, 'extra_vars', None):
        extra_vars: dict[str, t.Any] = {}
        for extra_vars_opt in context.CLIARGS.get('extra_vars', tuple()):
            extra_vars_opt = to_text(extra_vars_opt, errors='surrogate_or_strict')
            if extra_vars_opt is None or not extra_vars_opt:
                continue

            if extra_vars_opt.startswith(u"@"):
                # Argument is a YAML file (JSON is a subset of YAML)
                data = loader.load_from_file(extra_vars_opt[1:], trusted_as_template=True)
            elif extra_vars_opt[0] in [u'/', u'.']:
                raise AnsibleOptionsError("Please prepend extra_vars filename '%s' with '@'" % extra_vars_opt)
            elif extra_vars_opt[0] in [u'[', u'{']:
                # Arguments as YAML
                data = loader.load(extra_vars_opt)
            else:
                # Arguments as Key-value
                data = parse_kv(extra_vars_opt)

            if isinstance(data, MutableMapping):
                extra_vars = combine_vars(extra_vars, data)
            else:
                raise AnsibleOptionsError("Invalid extra vars data supplied. '%s' could not be made into a dictionary" % extra_vars_opt)

        load_extra_vars.extra_vars = extra_vars

    return load_extra_vars.extra_vars