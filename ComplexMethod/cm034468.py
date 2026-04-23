def get_remote_head(git_path, module, dest, version, remote, bare):
    cloning = False
    cwd = None
    tag = False
    if remote == module.params['repo']:
        cloning = True
    elif remote == 'file://' + os.path.expanduser(module.params['repo']):
        cloning = True
    else:
        cwd = dest
    if version == 'HEAD':
        if cloning:
            # cloning the repo, just get the remote's HEAD version
            cmd = '%s ls-remote %s -h HEAD' % (git_path, remote)
        else:
            head_branch = get_head_branch(git_path, module, dest, remote, bare)
            cmd = '%s ls-remote %s -h refs/heads/%s' % (git_path, remote, head_branch)
    elif is_remote_branch(git_path, module, dest, remote, version):
        cmd = '%s ls-remote %s -h refs/heads/%s' % (git_path, remote, version)
    elif is_remote_tag(git_path, module, dest, remote, version):
        tag = True
        cmd = '%s ls-remote %s -t refs/tags/%s*' % (git_path, remote, version)
    else:
        # Appears to be a sha hash. Checking requires special action
        rev = get_sha_hash(module, git_path, remote, version, cwd)

        return rev

    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=cwd)
    if len(out) < 1:
        module.fail_json(msg="Could not determine remote revision for %s" % version, stdout=out, stderr=err, rc=rc)

    out = to_native(out)

    if tag:
        # Find the dereferenced tag if this is an annotated tag.
        for tag in out.split('\n'):
            if tag.endswith(version + '^{}'):
                out = tag
                break
            elif tag.endswith(version):
                out = tag

    rev = out.split()[0]
    return rev