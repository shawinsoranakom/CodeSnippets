def __init__(self, args: Namespace) -> None:
        """Initialize the IssueResolver with the given parameters.

        Params initialized:
            owner: Owner of the repo.
            repo: Repository name.
            token: Token to access the repository.
            username: Username to access the repository.
            platform: Platform of the repository.
            runtime_container_image: Container image to use.
            max_iterations: Maximum number of iterations to run.
            output_dir: Output directory to write the results.
            llm_config: Configuration for the language model.
            prompt_template: Prompt template to use.
            issue_type: Type of issue to resolve (issue or pr).
            repo_instruction: Repository instruction to use.
            issue_number: Issue number to resolve.
            comment_id: Optional ID of a specific comment to focus on.
            base_domain: The base domain for the git server.
        """
        parts = args.selected_repo.rsplit('/', 1)
        if len(parts) < 2:
            raise ValueError('Invalid repository format. Expected owner/repo')
        owner, repo = parts

        token = (
            args.token
            or os.getenv('GITHUB_TOKEN')
            or os.getenv('GITLAB_TOKEN')
            or os.getenv('BITBUCKET_TOKEN')
            or os.getenv('AZURE_DEVOPS_TOKEN')
            or os.getenv('FORGEJO_TOKEN')
        )
        username = args.username if args.username else os.getenv('GIT_USERNAME')
        if not username:
            raise ValueError('Username is required.')

        if not token:
            raise ValueError('Token is required.')

        platform = call_async_from_sync(
            identify_token,
            GENERAL_TIMEOUT,
            token,
            args.base_domain,
        )

        repo_instruction = None
        if args.repo_instruction_file:
            with open(args.repo_instruction_file, 'r') as f:
                repo_instruction = f.read()

        issue_type = args.issue_type

        # Read the prompt template
        prompt_file = args.prompt_file
        if prompt_file is None:
            if issue_type == 'issue':
                prompt_file = os.path.join(
                    os.path.dirname(__file__), 'prompts/resolve/basic-with-tests.jinja'
                )
            else:
                prompt_file = os.path.join(
                    os.path.dirname(__file__), 'prompts/resolve/basic-followup.jinja'
                )
        with open(prompt_file, 'r') as f:
            user_instructions_prompt_template = f.read()

        with open(
            prompt_file.replace('.jinja', '-conversation-instructions.jinja')
        ) as f:
            conversation_instructions_prompt_template = f.read()

        base_domain = args.base_domain
        if base_domain is None:
            base_domain = (
                'github.com'
                if platform == ProviderType.GITHUB
                else 'gitlab.com'
                if platform == ProviderType.GITLAB
                else 'bitbucket.org'
                if platform == ProviderType.BITBUCKET
                else 'bitbucket.example.com'
                if platform == ProviderType.BITBUCKET_DATA_CENTER
                else 'dev.azure.com'
            )

        self.output_dir = args.output_dir
        self.issue_type = issue_type
        self.issue_number = args.issue_number

        self.workspace_base = self.build_workspace_base(
            self.output_dir, self.issue_type, self.issue_number
        )

        self.max_iterations = args.max_iterations

        self.app_config = self.update_openhands_config(
            load_openhands_config(),
            self.max_iterations,
            self.workspace_base,
            args.base_container_image,
            args.runtime_container_image,
            args.is_experimental,
            args.runtime,
        )

        self.owner = owner
        self.repo = repo
        self.platform = platform
        self.user_instructions_prompt_template = user_instructions_prompt_template
        self.conversation_instructions_prompt_template = (
            conversation_instructions_prompt_template
        )
        self.repo_instruction = repo_instruction
        self.comment_id = args.comment_id

        factory = IssueHandlerFactory(
            owner=self.owner,
            repo=self.repo,
            token=token,
            username=username,
            platform=self.platform,
            base_domain=base_domain,
            issue_type=self.issue_type,
            llm_config=self.app_config.get_llm_config(),
        )
        self.issue_handler = factory.create()