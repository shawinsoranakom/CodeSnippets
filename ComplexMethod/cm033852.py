def _get_shebang(
    interpreter: str,
    task_vars: dict[str, t.Any],
    templar: _template.Templar,
    args: tuple[str, ...] = tuple(),
    remote_is_local: bool = False,
    default_interpreters: dict[str, str] | None = None,
) -> tuple[str, str]:
    """
      Handles the different ways ansible allows overriding the shebang target for a module.
    """
    # FUTURE: add logical equivalence for python3 in the case of py3-only modules

    # For backwards compatibility we can adjust #!powershell using the pwsh
    # interpreter vars.
    if interpreter == 'powershell':
        interpreter_name = 'pwsh'
    else:
        interpreter_name = os.path.basename(interpreter).strip()

    # name for interpreter var
    interpreter_config = u'ansible_%s_interpreter' % interpreter_name
    # key for config
    interpreter_config_key = "INTERPRETER_%s" % interpreter_name.upper()

    interpreter_out: str | None = None

    # looking for python, rest rely on matching vars
    if interpreter_name == 'python':
        # skip detection for network os execution, use playbook supplied one if possible
        if remote_is_local:
            interpreter_out = task_vars['ansible_playbook_python']

        # a config def exists for this interpreter type; consult config for the value
        elif C.config.get_configuration_definition(interpreter_config_key):

            interpreter_from_config = C.config.get_config_value(interpreter_config_key, variables=task_vars)
            interpreter_out = templar._engine.template(_utils.str_problematic_strip(interpreter_from_config),
                                                       options=TemplateOptions(value_for_omit=C.config.get_config_default(interpreter_config_key)))

            # handle interpreter discovery if requested or empty interpreter was provided
            if not interpreter_out or interpreter_out in ['auto', 'auto_silent']:

                discovered_interpreter_config = u'discovered_interpreter_%s' % interpreter_name
                facts_from_task_vars = task_vars.get('ansible_facts', {})

                if discovered_interpreter_config not in facts_from_task_vars:
                    # interpreter discovery is desired, but has not been run for this host
                    raise InterpreterDiscoveryRequiredError("interpreter discovery needed", interpreter_name=interpreter_name, discovery_mode=interpreter_out)
                else:
                    interpreter_out = facts_from_task_vars[discovered_interpreter_config]
        else:
            raise InterpreterDiscoveryRequiredError("interpreter discovery required", interpreter_name=interpreter_name, discovery_mode='auto')

    elif interpreter_config in task_vars:
        # for non python we consult vars for a possible direct override
        interpreter_out = templar._engine.template(_utils.str_problematic_strip(task_vars.get(interpreter_config)),
                                                   options=TemplateOptions(value_for_omit=None))

    if not interpreter_out:
        # nothing matched(None) or in case someone configures empty string or empty interpreter
        default_interpreters = default_interpreters or {}
        interpreter_out = default_interpreters.get(interpreter, interpreter)

    # set shebang
    shebang = u'#!{0}'.format(interpreter_out)
    if args:
        shebang = shebang + u' ' + u' '.join(args)

    return shebang, interpreter_out