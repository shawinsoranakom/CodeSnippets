def clone(git_path, module, repo, dest, remote, depth, version, bare,
          reference, refspec, git_version_used, verify_commit, separate_git_dir, result, gpg_allowlist, single_branch):
    """ makes a new git repo if it does not already exist """
    dest_dirname = os.path.dirname(dest)
    try:
        os.makedirs(dest_dirname)
    except Exception:
        pass
    cmd = [git_path, 'clone']

    if bare:
        cmd.append('--bare')
    else:
        cmd.extend(['--origin', remote])

    is_branch_or_tag = is_remote_branch(git_path, module, dest, repo, version) or is_remote_tag(git_path, module, dest, repo, version)
    if depth:
        if version == 'HEAD' or refspec:
            cmd.extend(['--depth', str(depth)])
        elif is_branch_or_tag:
            cmd.extend(['--depth', str(depth)])
            cmd.extend(['--branch', version])
        else:
            # only use depth if the remote object is branch or tag (i.e. fetchable)
            module.warn("Ignoring depth argument. "
                        "Shallow clones are only available for "
                        "HEAD, branches, tags or in combination with refspec.")
    if reference:
        cmd.extend(['--reference', str(reference)])

    if single_branch:
        if git_version_used is None:
            module.fail_json(msg='Cannot find git executable at %s' % git_path)

        if git_version_used < LooseVersion('1.7.10'):
            module.warn("git version '%s' is too old to use 'single-branch'. Ignoring." % git_version_used)
        else:
            cmd.append("--single-branch")

            if is_branch_or_tag:
                cmd.extend(['--branch', version])

    needs_separate_git_dir_fallback = False
    if separate_git_dir:
        if git_version_used is None:
            module.fail_json(msg='Cannot find git executable at %s' % git_path)
        if git_version_used < LooseVersion('1.7.5'):
            # git before 1.7.5 doesn't have separate-git-dir argument, do fallback
            needs_separate_git_dir_fallback = True
        else:
            cmd.append('--separate-git-dir=%s' % separate_git_dir)

    cmd.extend([repo, dest])
    module.run_command(cmd, check_rc=True, cwd=dest_dirname)
    if needs_separate_git_dir_fallback:
        relocate_repo(module, result, separate_git_dir, os.path.join(dest, ".git"), dest)

    if bare and remote != 'origin':
        module.run_command([git_path, 'remote', 'add', remote, repo], check_rc=True, cwd=dest)

    if refspec:
        cmd = [git_path, 'fetch']
        if depth:
            cmd.extend(['--depth', str(depth)])
        cmd.extend([remote, refspec])
        module.run_command(cmd, check_rc=True, cwd=dest)

    if verify_commit:
        verify_commit_sign(git_path, module, dest, version, gpg_allowlist)