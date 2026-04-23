def _configure_repos(base, disablerepo_list, enablerepo_list, disable_gpg_check):
    """Enable and disable repositories matching the provided patterns."""
    repos = base.repos

    for repo_pattern in disablerepo_list:
        if repo_pattern:
            for repo in repos.get_matching(repo_pattern):
                repo.disable()

    for repo_pattern in enablerepo_list:
        if repo_pattern:
            for repo in repos.get_matching(repo_pattern):
                repo.enable()

    if disable_gpg_check:
        for repo in base.repos.iter_enabled():
            repo.gpgcheck = False
            repo.repo_gpgcheck = False