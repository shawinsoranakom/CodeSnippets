def set_git_ssh_env(key_file, ssh_opts, git_version, module):
    """
        use environment variables to configure git's ssh execution,
        which varies by version but this function should handle all.
    """

    # initialise to existing ssh opts and/or append user provided
    if ssh_opts is None:
        ssh_opts = os.environ.get('GIT_SSH_OPTS', '')
    else:
        ssh_opts = os.environ.get('GIT_SSH_OPTS', '') + ' ' + ssh_opts

    # hostkey acceptance
    accept_key = "StrictHostKeyChecking=no"
    if module.params['accept_hostkey'] and accept_key not in ssh_opts:
        ssh_opts += " -o %s" % accept_key

    # avoid prompts
    force_batch = 'BatchMode=yes'
    if force_batch not in ssh_opts:
        ssh_opts += ' -o %s' % (force_batch)

    # deal with key file
    if key_file:
        key_opt = '-i %s' % key_file
        if key_opt not in ssh_opts:
            ssh_opts += '  %s' % key_opt

        ikey = 'IdentitiesOnly=yes'
        if ikey not in ssh_opts:
            ssh_opts += ' -o %s' % ikey

    # older than 2.3 does not know how to use git_ssh_command,
    # so we force it into get_ssh var
    # https://github.com/gitster/git/commit/09d60d785c68c8fa65094ecbe46fbc2a38d0fc1f
    if git_version is not None and git_version < LooseVersion('2.3.0'):
        # for use in wrapper
        os.environ["GIT_SSH_OPTS"] = ssh_opts

        # these versions don't support GIT_SSH_OPTS so have to write wrapper
        wrapper = write_ssh_wrapper(module)

        # force use of git_ssh_opts via wrapper, git_ssh cannot not handle arguments
        os.environ['GIT_SSH'] = wrapper
    else:
        # we construct full finalized command string here
        full_cmd = os.environ.get('GIT_SSH', os.environ.get('GIT_SSH_COMMAND', 'ssh'))
        if ssh_opts:
            full_cmd += ' ' + ssh_opts
        # git_ssh_command can handle arguments to ssh
        os.environ["GIT_SSH_COMMAND"] = full_cmd