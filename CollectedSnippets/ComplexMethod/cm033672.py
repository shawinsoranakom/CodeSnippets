def check_pyyaml(python: PythonConfig, required: bool = True, quiet: bool = False) -> t.Optional[bool]:
    """
    Return True if PyYAML has libyaml support, False if it does not and None if it was not found.
    The result is cached if True or required.
    """
    try:
        return CHECK_YAML_VERSIONS[python.path]
    except KeyError:
        pass

    state = yamlcheck(python)

    if state is not None or required:
        # results are cached only if pyyaml is required or present
        # it is assumed that tests will not uninstall/re-install pyyaml -- if they do, those changes will go undetected
        CHECK_YAML_VERSIONS[python.path] = state

    if not quiet:
        if state is None:
            if required:
                display.warning('PyYAML is not installed for interpreter: %s' % python.path)
        elif not state:
            display.warning('PyYAML will be slow due to installation without libyaml support for interpreter: %s' % python.path)

    return state