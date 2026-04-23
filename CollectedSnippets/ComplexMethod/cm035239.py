async def clone_or_init_git_repo(
        self,
        task: AppConversationStartTask,
        workspace: AsyncRemoteWorkspace,
    ):
        request = task.request

        # Create the projects directory if it does not exist yet
        parent = Path(workspace.working_dir).parent
        result = await workspace.execute_command(
            f'mkdir -p {workspace.working_dir}', parent
        )
        if result.exit_code:
            _logger.warning(f'mkdir failed: {result.stderr}')

        # Configure git user settings from user preferences
        await self._configure_git_user_settings(workspace)

        if not request.selected_repository:
            if self.init_git_in_empty_workspace:
                _logger.debug('Initializing a new git repository in the workspace.')
                cmd = (
                    'git init && git config --global '
                    f'--add safe.directory {workspace.working_dir}'
                )
                result = await workspace.execute_command(cmd, workspace.working_dir)
                if result.exit_code:
                    _logger.warning(f'Git init failed: {result.stderr}')
            else:
                _logger.info('Not initializing a new git repository.')
            return

        remote_repo_url: str = await self.user_context.get_authenticated_git_url(
            request.selected_repository
        )
        if not remote_repo_url:
            raise ValueError('Missing either Git token or valid repository')

        dir_name = request.selected_repository.split('/')[-1]
        quoted_remote_repo_url = shlex.quote(remote_repo_url)
        quoted_dir_name = shlex.quote(dir_name)

        # Clone the repo - this is the slow part!
        clone_command = f'git clone {quoted_remote_repo_url} {quoted_dir_name}'
        result = await workspace.execute_command(
            clone_command, workspace.working_dir, 120
        )
        if result.exit_code:
            _logger.warning(f'Git clone failed: {result.stderr}')

        # Checkout the appropriate branch
        if request.selected_branch:
            ensure_valid_git_branch_name(request.selected_branch)
            checkout_command = f'git checkout {shlex.quote(request.selected_branch)}'
        else:
            # Generate a random branch name to avoid conflicts
            random_str = base62.encodebytes(os.urandom(16))
            openhands_workspace_branch = f'openhands-workspace-{random_str}'
            checkout_command = (
                f'git checkout -b {shlex.quote(openhands_workspace_branch)}'
            )
        git_dir = Path(workspace.working_dir) / dir_name
        result = await workspace.execute_command(checkout_command, git_dir)
        if result.exit_code:
            _logger.warning(f'Git checkout failed: {result.stderr}')