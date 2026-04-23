def switch_version(git_path, module, dest, remote, version, verify_commit, depth, gpg_allowlist):
    cmd = ''
    if version == 'HEAD':
        branch = get_head_branch(git_path, module, dest, remote)
        (rc, out, err) = module.run_command("%s checkout --force %s" % (git_path, branch), cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to checkout branch %s" % branch,
                             stdout=out, stderr=err, rc=rc)
        cmd = "%s reset --hard %s/%s --" % (git_path, remote, branch)
    else:
        # FIXME check for local_branch first, should have been fetched already
        if is_remote_branch(git_path, module, dest, remote, version):
            if depth and not is_local_branch(git_path, module, dest, version):
                # git clone --depth implies --single-branch, which makes
                # the checkout fail if the version changes
                # fetch the remote branch, to be able to check it out next
                set_remote_branch(git_path, module, dest, remote, version, depth)
            if not is_local_branch(git_path, module, dest, version):
                cmd = "%s checkout --track -b %s %s/%s" % (git_path, version, remote, version)
            else:
                (rc, out, err) = module.run_command("%s checkout --force %s" % (git_path, version), cwd=dest)
                if rc != 0:
                    module.fail_json(msg="Failed to checkout branch %s" % version, stdout=out, stderr=err, rc=rc)
                cmd = "%s reset --hard %s/%s" % (git_path, remote, version)
        else:
            cmd = "%s checkout --force %s" % (git_path, version)
    (rc, out1, err1) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        if version != 'HEAD':
            module.fail_json(msg="Failed to checkout %s" % (version),
                             stdout=out1, stderr=err1, rc=rc, cmd=cmd)
        else:
            module.fail_json(msg="Failed to checkout branch %s" % (branch),
                             stdout=out1, stderr=err1, rc=rc, cmd=cmd)

    if verify_commit:
        verify_commit_sign(git_path, module, dest, version, gpg_allowlist)

    return (rc, out1, err1)