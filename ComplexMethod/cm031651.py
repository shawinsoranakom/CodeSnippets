def get_git_upstream_remote():
    """
    Get the remote name to use for upstream branches

    Check for presence of "https://github.com/python/cpython" remote URL.
    If only one is found, return that remote name. If multiple are found,
    check for and return "upstream", "origin", or "python", in that
    order. Raise an error if no valid matches are found.
    """
    cmd = "git remote -v".split()
    output = subprocess.check_output(
        cmd,
        stderr=subprocess.DEVNULL,
        cwd=SRCDIR,
        encoding="UTF-8"
    )
    # Filter to desired remotes, accounting for potential uppercasing
    filtered_remotes = {
        remote.split("\t")[0].lower() for remote in output.split('\n')
        if "python/cpython" in remote.lower() and remote.endswith("(fetch)")
    }
    if len(filtered_remotes) == 1:
        [remote] = filtered_remotes
        return remote
    for remote_name in ["upstream", "origin", "python"]:
        if remote_name in filtered_remotes:
            return remote_name
    remotes_found = "\n".join(
        {remote for remote in output.split('\n') if remote.endswith("(fetch)")}
    )
    raise ValueError(
        f"Patchcheck was unable to find an unambiguous upstream remote, "
        f"with URL matching 'https://github.com/python/cpython'. "
        f"For help creating an upstream remote, see Dev Guide: "
        f"https://devguide.python.org/getting-started/"
        f"git-boot-camp/#cloning-a-forked-cpython-repository "
        f"\nRemotes found: \n{remotes_found}"
        )