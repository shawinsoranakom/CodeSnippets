def fetch(git_path, module, repo, dest, version, remote, depth, bare, refspec, git_version_used, force=False):
    """ updates repo from remote sources """
    set_remote_url(git_path, module, repo, dest, remote)
    commands = []

    fetch_str = 'download remote objects and refs'
    fetch_cmd = [git_path, 'fetch']

    refspecs = []
    if depth:
        # try to find the minimal set of refs we need to fetch to get a
        # successful checkout
        currenthead = get_head_branch(git_path, module, dest, remote)
        if refspec:
            refspecs.append(refspec)
        elif version == 'HEAD':
            refspecs.append(currenthead)
        elif is_remote_branch(git_path, module, dest, repo, version):
            if currenthead != version:
                # this workaround is only needed for older git versions
                # 1.8.3 is broken, 1.9.x works
                # ensure that remote branch is available as both local and remote ref
                refspecs.append('+refs/heads/%s:refs/heads/%s' % (version, version))
            refspecs.append('+refs/heads/%s:refs/remotes/%s/%s' % (version, remote, version))
        elif is_remote_tag(git_path, module, dest, repo, version):
            refspecs.append('+refs/tags/' + version + ':refs/tags/' + version)
        if refspecs:
            # if refspecs is empty, i.e. version is neither heads nor tags
            # assume it is a version hash
            # fall back to a full clone, otherwise we might not be able to checkout
            # version
            fetch_cmd.extend(['--depth', str(depth)])

    if not depth or not refspecs:
        # don't try to be minimalistic but do a full clone
        # also do this if depth is given, but version is something that can't be fetched directly
        if bare:
            refspecs = ['+refs/heads/*:refs/heads/*', '+refs/tags/*:refs/tags/*']
        else:
            # ensure all tags are fetched
            if git_version_used is not None and git_version_used >= LooseVersion('1.9'):
                fetch_cmd.append('--tags')
            else:
                # old git versions have a bug in --tags that prevents updating existing tags
                commands.append((fetch_str, fetch_cmd + [remote]))
                refspecs = ['+refs/tags/*:refs/tags/*']
        if refspec:
            refspecs.append(refspec)

    if force:
        fetch_cmd.append('--force')

    fetch_cmd.extend([remote])

    commands.append((fetch_str, fetch_cmd + refspecs))

    for (label, command) in commands:
        (rc, out, err) = module.run_command(command, cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to %s: %s %s" % (label, out, err), cmd=command)