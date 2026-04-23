def _git_repo_info(repo_path):
    """ returns a string containing git branch, commit id and commit date """
    result = None
    if os.path.exists(repo_path):
        # Check if the .git is a file. If it is a file, it means that we are in a submodule structure.
        if os.path.isfile(repo_path):
            try:
                with open(repo_path) as f:
                    gitdir = yaml_load(f).get('gitdir')
                # There is a possibility the .git file to have an absolute path.
                if os.path.isabs(gitdir):
                    repo_path = gitdir
                else:
                    repo_path = os.path.join(repo_path[:-4], gitdir)
            except (OSError, AttributeError):
                return ''
        with open(os.path.join(repo_path, "HEAD")) as f:
            line = f.readline().rstrip("\n")
            if line.startswith("ref:"):
                branch_path = os.path.join(repo_path, line[5:])
            else:
                branch_path = None
        if branch_path and os.path.exists(branch_path):
            branch = '/'.join(line.split('/')[2:])
            with open(branch_path) as f:
                commit = f.readline()[:10]
        else:
            # detached HEAD
            commit = line[:10]
            branch = 'detached HEAD'
            branch_path = os.path.join(repo_path, "HEAD")

        date = time.localtime(os.stat(branch_path).st_mtime)
        if time.daylight == 0:
            offset = time.timezone
        else:
            offset = time.altzone
        result = "({0} {1}) last updated {2} (GMT {3:+04d})".format(branch, commit, time.strftime("%Y/%m/%d %H:%M:%S", date), int(offset / -36))
    else:
        result = ''
    return result