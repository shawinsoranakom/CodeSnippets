async def clone_or_init_repo(
        self,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None,
        selected_repository: str | None,
        selected_branch: str | None,
    ) -> str:
        if not selected_repository:
            if self.config.init_git_in_empty_workspace:
                logger.debug(
                    'No repository selected. Initializing a new git repository in the workspace.'
                )
                action = CmdRunAction(
                    command=f'git init && git config --global --add safe.directory {self.workspace_root}'
                )
                await call_sync_from_async(self.run_action, action)
            else:
                logger.info(
                    'In workspace mount mode, not initializing a new git repository.'
                )
            return ''

        remote_repo_url = await self.provider_handler.get_authenticated_git_url(
            selected_repository
        )

        if not remote_repo_url:
            raise ValueError('Missing either Git token or valid repository')

        if self.status_callback:
            self.status_callback(
                'info', RuntimeStatus.SETTING_UP_WORKSPACE, 'Setting up workspace...'
            )

        dir_name = selected_repository.split('/')[-1]

        # Generate a random branch name to avoid conflicts
        random_str = ''.join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        openhands_workspace_branch = f'openhands-workspace-{random_str}'

        repo_path = self.workspace_root / dir_name
        quoted_repo_path = shlex.quote(str(repo_path))
        quoted_remote_repo_url = shlex.quote(remote_repo_url)

        # Clone repository command
        clone_command = f'git clone {quoted_remote_repo_url} {quoted_repo_path}'

        # Checkout to appropriate branch
        checkout_command = (
            f'git checkout {selected_branch}'
            if selected_branch
            else f'git checkout -b {openhands_workspace_branch}'
        )

        clone_action = CmdRunAction(command=clone_command)
        await call_sync_from_async(self.run_action, clone_action)

        cd_checkout_action = CmdRunAction(
            command=f'cd {quoted_repo_path} && {checkout_command}'
        )
        action = cd_checkout_action
        self.log('info', f'Cloning repo: {selected_repository}')
        await call_sync_from_async(self.run_action, action)

        if remote_repo_url:
            set_remote_action = CmdRunAction(
                command=(
                    f'cd {quoted_repo_path} && '
                    f'git remote set-url origin {quoted_remote_repo_url}'
                )
            )
            obs = await call_sync_from_async(self.run_action, set_remote_action)
            if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
                self.log(
                    'info',
                    f'Set git remote origin to authenticated URL for {selected_repository}',
                )
            else:
                self.log(
                    'warning',
                    (
                        'Failed to set git remote origin while ensuring fresh token '
                        f'for {selected_repository}: '
                        f'{obs.content if isinstance(obs, CmdOutputObservation) else "unknown error"}'
                    ),
                )

        return dir_name