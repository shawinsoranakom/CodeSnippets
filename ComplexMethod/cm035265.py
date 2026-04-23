def update_existing_pull_request(
    issue: Issue,
    token: str,
    username: str | None,
    platform: ProviderType,
    patch_dir: str,
    llm_config: LLMConfig,
    comment_message: str | None = None,
    additional_message: str | None = None,
    base_domain: str | None = None,
) -> str:
    """Update an existing pull request with the new patches.

    Args:
        issue: The issue to update.
        token: The  token to use for authentication.
        username: The username to use for authentication.
        platform: The platform of the repository.
        patch_dir: The directory containing the patches to apply.
        llm_config: The LLM configuration to use for summarizing changes.
        comment_message: The main message to post as a comment on the PR.
        additional_message: The additional messages to post as a comment on the PR in json list format.
        base_domain: The base domain for the git server (defaults to "github.com" for GitHub, "gitlab.com" for GitLab, and "dev.azure.com" for Azure DevOps)
    """
    # Set up headers and base URL for GitHub or GitLab API

    # Determine default base_domain based on platform
    if base_domain is None:
        base_domain = {
            ProviderType.GITHUB: 'github.com',
            ProviderType.GITLAB: 'gitlab.com',
            ProviderType.AZURE_DEVOPS: 'dev.azure.com',
            ProviderType.BITBUCKET: 'bitbucket.org',
            ProviderType.FORGEJO: 'codeberg.org',
            ProviderType.BITBUCKET_DATA_CENTER: 'bitbucket.example.com',
        }.get(platform, 'github.com')

    handler = None
    if platform == ProviderType.GITHUB:
        handler = ServiceContextIssue(
            GithubIssueHandler(issue.owner, issue.repo, token, username, base_domain),
            llm_config,
        )
    elif platform == ProviderType.GITLAB:
        handler = ServiceContextIssue(
            GitlabIssueHandler(issue.owner, issue.repo, token, username, base_domain),
            llm_config,
        )
    elif platform == ProviderType.AZURE_DEVOPS:
        # For Azure DevOps, owner is "organization/project"
        organization, project = issue.owner.split('/')
        handler = ServiceContextIssue(
            AzureDevOpsIssueHandler(token, organization, project, issue.repo),
            llm_config,
        )
    elif platform == ProviderType.BITBUCKET:
        handler = ServiceContextIssue(
            BitbucketIssueHandler(
                issue.owner, issue.repo, token, username, base_domain
            ),
            llm_config,
        )
    elif platform == ProviderType.BITBUCKET_DATA_CENTER:
        handler = ServiceContextIssue(
            BitbucketDCIssueHandler(
                issue.owner, issue.repo, token, username, base_domain
            ),
            llm_config,
        )
    elif platform == ProviderType.FORGEJO:
        handler = ServiceContextIssue(
            ForgejoIssueHandler(issue.owner, issue.repo, token, username, base_domain),
            llm_config,
        )
    else:
        raise ValueError(f'Unsupported platform: {platform}')

    branch_name = issue.head_branch

    # Prepare the push command
    push_command = (
        f'git -C {patch_dir} push '
        f'{handler.get_authorize_url()}'
        f'{issue.owner}/{issue.repo}.git {branch_name}'
    )

    # Push the changes to the existing branch
    result = subprocess.run(push_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f'Error pushing changes: {result.stderr}')
        raise RuntimeError('Failed to push changes to the remote repository')

    pr_url = handler.get_pull_url(issue.number)
    logger.info(f'Updated pull request {pr_url} with new patches.')

    # Generate a summary of all comment success indicators for PR message
    if not comment_message and additional_message:
        try:
            explanations = json.loads(additional_message)
            if explanations:
                comment_message = (
                    'OpenHands made the following changes to resolve the issues:\n\n'
                )
                for explanation in explanations:
                    comment_message += f'- {explanation}\n'

                # Summarize with LLM if provided
                if llm_config is not None:
                    llm = LLM(llm_config, service_id='resolver')
                    with open(
                        os.path.join(
                            os.path.dirname(__file__),
                            'prompts/resolve/pr-changes-summary.jinja',
                        ),
                        'r',
                    ) as f:
                        template = jinja2.Template(f.read())
                    prompt = template.render(comment_message=comment_message)
                    response = llm.completion(
                        messages=[{'role': 'user', 'content': prompt}],
                    )
                    comment_message = response.choices[0].message.content.strip()

        except (json.JSONDecodeError, TypeError):
            comment_message = (
                'A new OpenHands update is available, but failed to parse or summarize '
                f'the changes:\n{additional_message}'
            )

    # Post a comment on the PR
    if comment_message:
        handler.send_comment_msg(issue.number, comment_message)

    # Reply to each unresolved comment thread
    if additional_message and issue.thread_ids:
        try:
            explanations = json.loads(additional_message)
            for count, reply_comment in enumerate(explanations):
                comment_id = issue.thread_ids[count]
                handler.reply_to_comment(issue.number, comment_id, reply_comment)
        except (json.JSONDecodeError, TypeError):
            msg = f'Error occurred when replying to threads; success explanations {additional_message}'
            handler.send_comment_msg(issue.number, msg)

    return pr_url