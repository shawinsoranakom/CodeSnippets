def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type='path'),
            repo=dict(required=True, aliases=['name']),
            version=dict(default='HEAD'),
            remote=dict(default='origin'),
            refspec=dict(default=None),
            reference=dict(default=None),
            force=dict(default='no', type='bool'),
            depth=dict(default=None, type='int'),
            clone=dict(default='yes', type='bool'),
            update=dict(default='yes', type='bool'),
            verify_commit=dict(default='no', type='bool'),
            gpg_allowlist=dict(
                default=[], type='list', elements='str',
            ),
            accept_hostkey=dict(default='no', type='bool'),
            accept_newhostkey=dict(default='no', type='bool'),
            key_file=dict(default=None, type='path', required=False),
            ssh_opts=dict(default=None, required=False),
            executable=dict(default=None, type='path'),
            bare=dict(default='no', type='bool'),
            recursive=dict(default='yes', type='bool'),
            single_branch=dict(default=False, type='bool'),
            track_submodules=dict(default='no', type='bool'),
            umask=dict(default=None, type='raw'),
            archive=dict(type='path'),
            archive_prefix=dict(),
            separate_git_dir=dict(type='path'),
        ),
        mutually_exclusive=[('separate_git_dir', 'bare'), ('accept_hostkey', 'accept_newhostkey')],
        required_by={'archive_prefix': ['archive']},
        supports_check_mode=True
    )

    dest = module.params['dest']
    repo = module.params['repo']
    version = module.params['version']
    remote = module.params['remote']
    refspec = module.params['refspec']
    force = module.params['force']
    depth = module.params['depth']
    update = module.params['update']
    allow_clone = module.params['clone']
    bare = module.params['bare']
    verify_commit = module.params['verify_commit']
    gpg_allowlist = module.params['gpg_allowlist']
    reference = module.params['reference']
    single_branch = module.params['single_branch']
    git_path = module.params['executable'] or module.get_bin_path('git', True)
    key_file = module.params['key_file']
    ssh_opts = module.params['ssh_opts']
    umask = module.params['umask']
    archive = module.params['archive']
    archive_prefix = module.params['archive_prefix']
    separate_git_dir = module.params['separate_git_dir']

    result = dict(changed=False)

    if module.params['accept_hostkey']:
        if ssh_opts is not None:
            if ("-o StrictHostKeyChecking=no" not in ssh_opts) and ("-o StrictHostKeyChecking=accept-new" not in ssh_opts):
                ssh_opts += " -o StrictHostKeyChecking=no"
        else:
            ssh_opts = "-o StrictHostKeyChecking=no"

    if module.params['accept_newhostkey']:
        if not ssh_supports_acceptnewhostkey(module):
            module.warn("Your ssh client does not support accept_newhostkey option, therefore it cannot be used.")
        else:
            if ssh_opts is not None:
                if ("-o StrictHostKeyChecking=no" not in ssh_opts) and ("-o StrictHostKeyChecking=accept-new" not in ssh_opts):
                    ssh_opts += " -o StrictHostKeyChecking=accept-new"
            else:
                ssh_opts = "-o StrictHostKeyChecking=accept-new"

    # evaluate and set the umask before doing anything else
    if umask is not None:
        if not isinstance(umask, str):
            module.fail_json(msg="umask must be defined as a quoted octal integer")
        try:
            umask = int(umask, 8)
        except Exception:
            module.fail_json(msg="umask must be an octal integer",
                             details=to_text(sys.exc_info()[1]))
        os.umask(umask)

    # Certain features such as depth require a file:/// protocol for path based urls
    # so force a protocol here ...
    if os.path.expanduser(repo).startswith('/'):
        repo = 'file://' + os.path.expanduser(repo)

    # We screenscrape a huge amount of git commands so use C locale anytime we
    # call run_command()
    locale = get_best_parsable_locale(module)
    module.run_command_environ_update = dict(LANG=locale, LC_ALL=locale, LC_MESSAGES=locale, LC_CTYPE=locale, LANGUAGE=locale)

    if separate_git_dir:
        separate_git_dir = os.path.realpath(separate_git_dir)

    gitconfig = None
    if not dest and allow_clone:
        module.fail_json(msg="the destination directory must be specified unless clone=no")
    elif dest:
        dest = os.path.abspath(dest)
        try:
            repo_path = get_repo_path(dest, bare)
            if separate_git_dir and os.path.exists(repo_path) and separate_git_dir != repo_path:
                result['changed'] = True
                if not module.check_mode:
                    relocate_repo(module, result, separate_git_dir, repo_path, dest)
                    repo_path = separate_git_dir
        except (OSError, ValueError) as ex:
            # No repo path found
            # ``.git`` file does not have a valid format for detached Git dir.
            module.fail_json(
                msg='Current repo does not have a valid reference to a '
                'separate Git dir or it refers to the invalid path',
                details=str(ex),
                exception=ex,
            )
        gitconfig = os.path.join(repo_path, 'config')

    # iface changes so need it to make decisions
    git_version_used = git_version(git_path, module)

    # GIT_SSH=<path> as an environment variable, might create sh wrapper script for older versions.
    set_git_ssh_env(key_file, ssh_opts, git_version_used, module)

    if depth is not None and git_version_used is not None and git_version_used < LooseVersion('1.9.1'):
        module.warn("git version is too old to fully support the depth argument. Falling back to full checkouts.")
        depth = None

    recursive = module.params['recursive']
    track_submodules = module.params['track_submodules']

    result.update(before=None)

    local_mods = False
    if (dest and not os.path.exists(gitconfig)) or (not dest and not allow_clone):
        # if there is no git configuration, do a clone operation unless:
        # * the user requested no clone (they just want info)
        # * we're doing a check mode test
        # In those cases we do an ls-remote
        if module.check_mode or not allow_clone:
            remote_head = get_remote_head(git_path, module, dest, version, repo, bare)
            result.update(changed=True, after=remote_head)
            if module._diff:
                diff = get_diff(module, git_path, dest, repo, remote, depth, bare, result['before'], result['after'], refspec, force)
                if diff:
                    result['diff'] = diff
            module.exit_json(**result)
        # there's no git config, so clone
        clone(git_path, module, repo, dest, remote, depth, version, bare, reference,
              refspec, git_version_used, verify_commit, separate_git_dir, result, gpg_allowlist, single_branch)
    elif not update:
        # Just return having found a repo already in the dest path
        # this does no checking that the repo is the actual repo
        # requested.
        result['before'] = get_version(module, git_path, dest)
        result.update(after=result['before'])
        if archive:
            # Git archive is not supported by all git servers, so
            # we will first clone and perform git archive from local directory
            if module.check_mode:
                result.update(changed=True)
                module.exit_json(**result)

            create_archive(git_path, module, dest, archive, archive_prefix, version, repo, result)

        module.exit_json(**result)
    else:
        # else do a pull
        local_mods = has_local_mods(module, git_path, dest, bare)
        result['before'] = get_version(module, git_path, dest)
        if local_mods:
            # failure should happen regardless of check mode
            if not force:
                module.fail_json(msg="Local modifications exist in the destination: " + dest + " (force=no).", **result)
            # if force and in non-check mode, do a reset
            if not module.check_mode:
                reset(git_path, module, dest)
                result.update(changed=True, msg='Local modifications exist in the destination: ' + dest)

        # exit if already at desired sha version
        if module.check_mode:
            remote_url = get_remote_url(git_path, module, dest, remote)
            remote_url_changed = remote_url and remote_url != repo and unfrackgitpath(remote_url) != unfrackgitpath(repo)
        else:
            remote_url_changed = set_remote_url(git_path, module, repo, dest, remote)
        result.update(remote_url_changed=remote_url_changed)

        if module.check_mode:
            remote_head = get_remote_head(git_path, module, dest, version, remote, bare)
            result.update(changed=(result['before'] != remote_head or remote_url_changed), after=remote_head)
            # FIXME: This diff should fail since the new remote_head is not fetched yet?!
            if module._diff:
                diff = get_diff(module, git_path, dest, repo, remote, depth, bare, result['before'], result['after'], refspec, force)
                if diff:
                    result['diff'] = diff
            module.exit_json(**result)
        else:
            fetch(git_path, module, repo, dest, version, remote, depth, bare, refspec, git_version_used, force=force)

        result['after'] = get_version(module, git_path, dest)

    # switch to version specified regardless of whether
    # we got new revisions from the repository
    if not bare:
        switch_version(git_path, module, dest, remote, version, verify_commit, depth, gpg_allowlist)

    # Deal with submodules
    submodules_updated = False
    if recursive and not bare:
        submodules_updated = submodules_fetch(git_path, module, remote, track_submodules, dest)
        if submodules_updated:
            result.update(submodules_changed=submodules_updated)

            if module.check_mode:
                result.update(changed=True, after=remote_head)
                module.exit_json(**result)

            # Switch to version specified
            submodule_update(git_path, module, dest, track_submodules, force=force)

    # determine if we changed anything
    result['after'] = get_version(module, git_path, dest)

    if result['before'] != result['after'] or local_mods or submodules_updated or remote_url_changed:
        result.update(changed=True)
        if module._diff:
            diff = get_diff(module, git_path, dest, repo, remote, depth, bare, result['before'], result['after'], refspec, force)
            if diff:
                result['diff'] = diff

    if archive:
        # Git archive is not supported by all git servers, so
        # we will first clone and perform git archive from local directory
        if module.check_mode:
            result.update(changed=True)
            module.exit_json(**result)

        create_archive(git_path, module, dest, archive, archive_prefix, version, repo, result)

    module.exit_json(**result)