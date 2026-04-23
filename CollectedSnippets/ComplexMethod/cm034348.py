def _extract_collection_from_git(repo_url, coll_ver, b_path):
    name, version, git_url, fragment = parse_scm(repo_url, coll_ver)
    b_checkout_path = mkdtemp(
        dir=b_path,
        prefix=to_bytes(name, errors='surrogate_or_strict'),
    )

    try:
        git_executable = get_bin_path('git')
    except ValueError as err:
        raise AnsibleError(
            "Could not find git executable to extract the collection from the Git repository `{repo_url!s}`.".
            format(repo_url=to_native(git_url))
        ) from err

    # Perform a shallow clone if simply cloning HEAD
    if version == 'HEAD':
        git_clone_cmd = [git_executable, 'clone', '--depth=1', git_url, to_text(b_checkout_path)]
    else:
        git_clone_cmd = [git_executable, 'clone', git_url, to_text(b_checkout_path)]
    # FIXME: '--branch', version

    if context.CLIARGS['ignore_certs'] or C.GALAXY_IGNORE_CERTS:
        git_clone_cmd.extend(['-c', 'http.sslVerify=false'])

    try:
        subprocess.check_call(git_clone_cmd)
    except subprocess.CalledProcessError as proc_err:
        raise AnsibleError(  # should probably be LookupError
            'Failed to clone a Git repository from `{repo_url!s}`.'.
            format(repo_url=to_native(git_url)),
        ) from proc_err

    if version == 'HEAD':
        git_args = ()
    else:
        git_args = '-c', 'advice.detachedHead=false'

    git_switch_cmd = git_executable, *git_args, 'checkout', to_text(version)
    try:
        subprocess.check_call(git_switch_cmd, cwd=b_checkout_path)
    except subprocess.CalledProcessError as proc_err:
        raise AnsibleError(  # should probably be LookupError
            'Failed to switch a cloned Git repo `{repo_url!s}` '
            'to the requested revision `{revision!s}`.'.
            format(
                revision=to_native(version),
                repo_url=to_native(git_url),
            ),
        ) from proc_err

    return (
        os.path.join(b_checkout_path, to_bytes(fragment))
        if fragment else b_checkout_path
    )