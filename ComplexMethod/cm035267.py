def main() -> None:
    parser = argparse.ArgumentParser(
        description='Send a pull request to Github, Gitlab, or Azure DevOps.'
    )
    parser.add_argument(
        '--selected-repo',
        type=str,
        default=None,
        help='repository to send pull request in form of `owner/repo`.',
    )
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='token to access the repository.',
    )
    parser.add_argument(
        '--username',
        type=str,
        default=None,
        help='username to access the repository.',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory to write the results.',
    )
    parser.add_argument(
        '--pr-type',
        type=str,
        default='draft',
        choices=['branch', 'draft', 'ready'],
        help='Type of the pull request to send [branch, draft, ready]',
    )
    parser.add_argument(
        '--issue-number',
        type=str,
        required=True,
        help="Issue number to send the pull request for, or 'all_successful' to process all successful issues.",
    )
    parser.add_argument(
        '--fork-owner',
        type=str,
        default=None,
        help='Owner of the fork to push changes to (if different from the original repo owner).',
    )
    parser.add_argument(
        '--send-on-failure',
        action='store_true',
        help='Send a pull request even if the issue was not successfully resolved.',
    )
    parser.add_argument(
        '--llm-model',
        type=str,
        default=None,
        help='LLM model to use for summarizing changes.',
    )
    parser.add_argument(
        '--llm-api-key',
        type=str,
        default=None,
        help='API key for the LLM model.',
    )
    parser.add_argument(
        '--llm-base-url',
        type=str,
        default=None,
        help='Base URL for the LLM model.',
    )
    parser.add_argument(
        '--target-branch',
        type=str,
        default=None,
        help='Target branch to create the pull request against (defaults to repository default branch)',
    )
    parser.add_argument(
        '--reviewer',
        type=str,
        help='GitHub, GitLab, or Azure DevOps username of the person to request review from',
        default=None,
    )
    parser.add_argument(
        '--pr-title',
        type=str,
        help='Custom title for the pull request',
        default=None,
    )
    parser.add_argument(
        '--base-domain',
        type=str,
        default=None,
        help='Base domain for the git server (defaults to "github.com" for GitHub, "gitlab.com" for GitLab, and "dev.azure.com" for Azure DevOps)',
    )
    parser.add_argument(
        '--git-user-name',
        type=str,
        default='openhands',
        help='Git user name for commits',
    )
    parser.add_argument(
        '--git-user-email',
        type=str,
        default='openhands@all-hands.dev',
        help='Git user email for commits',
    )
    my_args = parser.parse_args()

    token = (
        my_args.token
        or os.getenv('GITHUB_TOKEN')
        or os.getenv('GITLAB_TOKEN')
        or os.getenv('AZURE_DEVOPS_TOKEN')
        or os.getenv('FORGEJO_TOKEN')
    )
    if not token:
        raise ValueError(
            'token is not set, set via --token or GITHUB_TOKEN, GITLAB_TOKEN, AZURE_DEVOPS_TOKEN, or FORGEJO_TOKEN environment variable.'
        )
    username = my_args.username if my_args.username else os.getenv('GIT_USERNAME')

    platform = call_async_from_sync(
        identify_token,
        GENERAL_TIMEOUT,
        token,
        my_args.base_domain,
    )

    api_key = my_args.llm_api_key or os.environ['LLM_API_KEY']
    model_name = my_args.llm_model or os.environ['LLM_MODEL']
    base_url = my_args.llm_base_url or os.environ.get('LLM_BASE_URL')
    resolved_base_url = get_effective_llm_base_url(
        model_name,
        base_url,
    )
    llm_config = LLMConfig(
        model=model_name,
        api_key=SecretStr(api_key) if api_key else None,
        base_url=resolved_base_url,
    )

    if not os.path.exists(my_args.output_dir):
        raise ValueError(f'Output directory {my_args.output_dir} does not exist.')

    if not my_args.issue_number.isdigit():
        raise ValueError(f'Issue number {my_args.issue_number} is not a number.')
    issue_number = int(my_args.issue_number)
    output_path = os.path.join(my_args.output_dir, 'output.jsonl')
    resolver_output = load_single_resolver_output(output_path, issue_number)
    if not username:
        raise ValueError('username is required.')
    process_single_issue(
        my_args.output_dir,
        resolver_output,
        token,
        username,
        platform,
        my_args.pr_type,
        llm_config,
        my_args.fork_owner,
        my_args.send_on_failure,
        my_args.target_branch,
        my_args.reviewer,
        my_args.pr_title,
        my_args.base_domain,
        my_args.git_user_name,
        my_args.git_user_email,
    )