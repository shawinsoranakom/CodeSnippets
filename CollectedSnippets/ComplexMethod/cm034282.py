def find_ini_config_file(warnings=None):
    """ Load INI Config File order(first found is used): ENV, CWD, HOME, /etc/ansible """
    # FIXME: eventually deprecate ini configs

    if warnings is None:
        # Note: In this case, warnings does nothing
        warnings = set()

    potential_paths = []

    # A value that can never be a valid path so that we can tell if ANSIBLE_CONFIG was set later
    # We can't use None because we could set path to None.
    # Environment setting
    path_from_env = os.getenv("ANSIBLE_CONFIG", Sentinel)
    if path_from_env is not Sentinel:
        path_from_env = unfrackpath(path_from_env, follow=False)
        if os.path.isdir(to_bytes(path_from_env)):
            path_from_env = os.path.join(path_from_env, "ansible.cfg")
        potential_paths.append(path_from_env)

    # Current working directory
    warn_cmd_public = False
    try:
        cwd = os.getcwd()
        perms = os.stat(cwd)
        cwd_cfg = os.path.join(cwd, "ansible.cfg")
        if perms.st_mode & stat.S_IWOTH:
            # Working directory is world writable so we'll skip it.
            # Still have to look for a file here, though, so that we know if we have to warn
            if os.path.exists(cwd_cfg):
                warn_cmd_public = True
        else:
            potential_paths.append(to_text(cwd_cfg, errors='surrogate_or_strict'))
    except OSError:
        # If we can't access cwd, we'll simply skip it as a possible config source
        pass

    # Per user location
    potential_paths.append(unfrackpath("~/.ansible.cfg", follow=False))

    # System location
    potential_paths.append("/etc/ansible/ansible.cfg")

    for path in potential_paths:
        b_path = to_bytes(path)
        if os.path.exists(b_path) and os.access(b_path, os.R_OK):
            break
    else:
        path = None

    # Emit a warning if all the following are true:
    # * We did not use a config from ANSIBLE_CONFIG
    # * There's an ansible.cfg in the current working directory that we skipped
    if path_from_env != path and warn_cmd_public:
        warnings.add(u"Ansible is being run in a world writable directory (%s),"
                     u" ignoring it as an ansible.cfg source."
                     u" For more information see"
                     u" https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir"
                     % to_text(cwd))

    return path