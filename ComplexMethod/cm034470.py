def submodules_fetch(git_path, module, remote, track_submodules, dest):
    changed = False

    if not os.path.exists(os.path.join(dest, '.gitmodules')):
        # no submodules
        return changed

    gitmodules_file = open(os.path.join(dest, '.gitmodules'), 'r')
    for line in gitmodules_file:
        # Check for new submodules
        if not changed and line.strip().startswith('path'):
            path = line.split('=', 1)[1].strip()
            # Check that dest/path/.git exists
            if not os.path.exists(os.path.join(dest, path, '.git')):
                changed = True

    # Check for updates to existing modules
    if not changed:
        # Fetch updates
        begin = get_submodule_versions(git_path, module, dest)
        cmd = [git_path, 'submodule', 'foreach', git_path, 'fetch']
        (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to fetch submodules: %s" % out + err)

        if track_submodules:
            # Compare each submodule against its configured remote branch
            after = {}
            for submodule in begin:
                branch = get_submodule_branch(git_path, module, dest, submodule)
                version_ref = f'{remote}/{branch}' if branch != 'HEAD' else 'HEAD'
                submodule_path = os.path.join(dest, submodule)
                cmd = [git_path, 'rev-parse', version_ref]
                (rc, out, err) = module.run_command(cmd, cwd=submodule_path)
                if rc != 0:
                    module.fail_json(
                        msg='Unable to determine hash of submodule %s at %s' % (submodule, version_ref),
                        stdout=out, stderr=err, rc=rc)
                after[submodule] = out.strip()
            if begin != after:
                changed = True
        else:
            # Compare against the superproject's expectation
            cmd = [git_path, 'submodule', 'status']
            (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
            if rc != 0:
                module.fail_json(msg='Failed to retrieve submodule status: %s' % out + err)
            for line in out.splitlines():
                if line[0] != ' ':
                    changed = True
                    break
    return changed