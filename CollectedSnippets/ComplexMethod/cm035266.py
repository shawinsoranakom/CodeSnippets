def process_single_issue(
    output_dir: str,
    resolver_output: ResolverOutput,
    token: str,
    username: str,
    platform: ProviderType,
    pr_type: str,
    llm_config: LLMConfig,
    fork_owner: str | None,
    send_on_failure: bool,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
    base_domain: str | None = None,
    git_user_name: str = 'openhands',
    git_user_email: str = 'openhands@all-hands.dev',
) -> None:
    # Determine default base_domain based on platform
    if base_domain is None:
        base_domain = (
            'github.com'
            if platform == ProviderType.GITHUB
            else 'gitlab.com'
            if platform == ProviderType.GITLAB
            else 'dev.azure.com'
            if platform == ProviderType.AZURE_DEVOPS
            else 'bitbucket.org'
            if platform == ProviderType.BITBUCKET
            else 'bitbucket.example.com'
            if platform == ProviderType.BITBUCKET_DATA_CENTER
            else 'github.com'
        )
    if not resolver_output.success and not send_on_failure:
        logger.info(
            f'Issue {resolver_output.issue.number} was not successfully resolved. Skipping PR creation.'
        )
        return

    issue_type = resolver_output.issue_type

    if issue_type == 'issue':
        patched_repo_dir = initialize_repo(
            output_dir,
            resolver_output.issue.number,
            issue_type,
            resolver_output.base_commit,
        )
    elif issue_type == 'pr':
        patched_repo_dir = initialize_repo(
            output_dir,
            resolver_output.issue.number,
            issue_type,
            resolver_output.issue.head_branch,
        )
    else:
        raise ValueError(f'Invalid issue type: {issue_type}')

    apply_patch(patched_repo_dir, resolver_output.git_patch)

    make_commit(
        patched_repo_dir,
        resolver_output.issue,
        issue_type,
        git_user_name,
        git_user_email,
    )

    if issue_type == 'pr':
        update_existing_pull_request(
            issue=resolver_output.issue,
            token=token,
            username=username,
            platform=platform,
            patch_dir=patched_repo_dir,
            additional_message=resolver_output.result_explanation,
            llm_config=llm_config,
            base_domain=base_domain,
        )
    else:
        send_pull_request(
            issue=resolver_output.issue,
            token=token,
            username=username,
            platform=platform,
            patch_dir=patched_repo_dir,
            pr_type=pr_type,
            fork_owner=fork_owner,
            additional_message=resolver_output.result_explanation,
            target_branch=target_branch,
            reviewer=reviewer,
            pr_title=pr_title,
            base_domain=base_domain,
            git_user_name=git_user_name,
            git_user_email=git_user_email,
        )