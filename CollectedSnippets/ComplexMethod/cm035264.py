def send_pull_request(
    issue: Issue,
    token: str,
    username: str | None,
    platform: ProviderType,
    patch_dir: str,
    pr_type: str,
    fork_owner: str | None = None,
    additional_message: str | None = None,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
    base_domain: str | None = None,
    git_user_name: str = 'openhands',
    git_user_email: str = 'openhands@all-hands.dev',
) -> str:
    """Send a pull request to a GitHub, GitLab, Bitbucket, Forgejo, or Azure DevOps repository.

    Args:
        issue: The issue to send the pull request for
        token: The token to use for authentication
        username: The username, if provided
        platform: The platform of the repository.
        patch_dir: The directory containing the patches to apply
        pr_type: The type: branch (no PR created), draft or ready (regular PR created)
        fork_owner: The owner of the fork to push changes to (if different from the original repo owner)
        additional_message: The additional messages to post as a comment on the PR in json list format
        target_branch: The target branch to create the pull request against (defaults to repository default branch)
        reviewer: The username of the reviewer to assign
        pr_title: Custom title for the pull request (optional)
        base_domain: The base domain for the git server (defaults to "github.com" for GitHub, "gitlab.com" for GitLab, "bitbucket.org" for Bitbucket, "codeberg.org" for Forgejo, and "dev.azure.com" for Azure DevOps)
        git_user_name: Git username to configure when creating commits
        git_user_email: Git email to configure when creating commits
    """
    if pr_type not in ['branch', 'draft', 'ready']:
        raise ValueError(f'Invalid pr_type: {pr_type}')

    # Determine default base_domain based on platform
    if base_domain is None:
        base_domain = {
            ProviderType.GITHUB: 'github.com',
            ProviderType.GITLAB: 'gitlab.com',
            ProviderType.BITBUCKET: 'bitbucket.org',
            ProviderType.FORGEJO: 'codeberg.org',
            ProviderType.AZURE_DEVOPS: 'dev.azure.com',
        }.get(platform, 'github.com')

    # Create the appropriate handler based on platform
    handler = None
    if platform == ProviderType.GITHUB:
        handler = ServiceContextIssue(
            GithubIssueHandler(issue.owner, issue.repo, token, username, base_domain),
            None,
        )
    elif platform == ProviderType.GITLAB:
        handler = ServiceContextIssue(
            GitlabIssueHandler(issue.owner, issue.repo, token, username, base_domain),
            None,
        )
    elif platform == ProviderType.BITBUCKET:
        handler = ServiceContextIssue(
            BitbucketIssueHandler(
                issue.owner, issue.repo, token, username, base_domain
            ),
            None,
        )
    elif platform == ProviderType.BITBUCKET_DATA_CENTER:
        handler = ServiceContextIssue(
            BitbucketDCIssueHandler(
                issue.owner, issue.repo, token, username, base_domain
            ),
            None,
        )
    elif platform == ProviderType.FORGEJO:
        handler = ServiceContextIssue(
            ForgejoIssueHandler(issue.owner, issue.repo, token, username, base_domain),
            None,
        )
    elif platform == ProviderType.AZURE_DEVOPS:
        # For Azure DevOps, owner is "organization/project"
        organization, project = issue.owner.split('/')
        handler = ServiceContextIssue(
            AzureDevOpsIssueHandler(token, organization, project, issue.repo),
            None,
        )
    else:
        raise ValueError(f'Unsupported platform: {platform}')

    # Create a new branch with a unique name
    base_branch_name = f'openhands-fix-issue-{issue.number}'
    branch_name = handler.get_branch_name(
        base_branch_name=base_branch_name,
    )

    # Get the default branch or use specified target branch
    logger.info('Getting base branch...')
    if target_branch:
        base_branch = target_branch
        exists = handler.branch_exists(branch_name=target_branch)
        if not exists:
            raise ValueError(f'Target branch {target_branch} does not exist')
    else:
        base_branch = handler.get_default_branch_name()
    logger.info(f'Base branch: {base_branch}')

    # Create and checkout the new branch
    logger.info('Creating new branch...')
    result = subprocess.run(
        ['git', '-C', patch_dir, 'checkout', '-b', branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f'Error creating new branch: {result.stderr}')
        raise RuntimeError(
            f'Failed to create a new branch {branch_name} in {patch_dir}:'
        )

    # Determine the repository to push to (original or fork)
    push_owner = fork_owner if fork_owner else issue.owner

    handler._strategy.set_owner(push_owner)

    logger.info('Pushing changes...')
    push_url = handler.get_clone_url()
    result = subprocess.run(
        ['git', '-C', patch_dir, 'push', push_url, branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f'Error pushing changes: {result.stderr}')
        raise RuntimeError('Failed to push changes to the remote repository')

    # Prepare the PR data: title and body
    final_pr_title = (
        pr_title if pr_title else f'Fix issue #{issue.number}: {issue.title}'
    )
    pr_body = f'This pull request fixes #{issue.number}.'
    if additional_message:
        pr_body += f'\n\n{additional_message}'
    pr_body += f'\n\n{PR_SIGNATURE}'

    # For cross repo pull request, we need to send head parameter like fork_owner:branch as per git documentation here : https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request
    # head parameter usage : The name of the branch where your changes are implemented. For cross-repository pull requests in the same network, namespace head with a user like this: username:branch.
    if fork_owner and platform in (ProviderType.GITHUB, ProviderType.FORGEJO):
        head_branch = f'{fork_owner}:{branch_name}'
    else:
        head_branch = branch_name
    # If we are not sending a PR, we can finish early and return the
    # URL for the user to open a PR manually
    if pr_type == 'branch':
        url = handler.get_compare_url(branch_name)
    else:
        # Prepare the PR for the GitHub API
        if platform == ProviderType.GITHUB:
            data = {
                'title': final_pr_title,
                'body': pr_body,
                'head': head_branch,
                'base': base_branch,
                'draft': pr_type == 'draft',
            }
        elif platform == ProviderType.GITLAB:
            data = {
                'title': final_pr_title,
                'description': pr_body,
                'source_branch': head_branch,
                'target_branch': base_branch,
                'draft': pr_type == 'draft',
            }
        elif platform == ProviderType.BITBUCKET:
            data = {
                'title': final_pr_title,
                'description': pr_body,
                'source_branch': head_branch,
                'target_branch': base_branch,
                'draft': pr_type == 'draft',
            }
        elif platform == ProviderType.BITBUCKET_DATA_CENTER:
            data = {
                'title': final_pr_title,
                'description': pr_body,
                'source_branch': head_branch,
                'target_branch': base_branch,
                'draft': pr_type == 'draft',
            }
        elif platform == ProviderType.FORGEJO:
            data = {
                'title': final_pr_title,
                'body': pr_body,
                'head': head_branch,
                'base': base_branch,
                'draft': pr_type == 'draft',
            }
        else:
            raise ValueError(f'Unsupported platform for PR creation: {platform}')

        pr_data = handler.create_pull_request(data)
        url = pr_data['html_url']

        # Request review if a reviewer was specified
        if reviewer and pr_type != 'branch':
            number = pr_data['number']
            handler.request_reviewers(reviewer, number)

    logger.info(
        f'{pr_type} created: {url}\n\n--- Title: {final_pr_title}\n\n--- Body:\n{pr_body}'
    )

    return url