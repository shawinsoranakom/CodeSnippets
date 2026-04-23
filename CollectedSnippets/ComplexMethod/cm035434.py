def get_microagents_from_org_or_user(
        self, selected_repository: str
    ) -> list[BaseMicroagent]:
        """Load microagents from the organization or user level repository.

        For example, if the repository is github.com/acme-co/api, this will check if
        github.com/acme-co/.openhands exists. If it does, it will clone it and load
        the microagents from the ./microagents/ folder.

        For GitLab repositories, it will use openhands-config instead of .openhands
        since GitLab doesn't support repository names starting with non-alphanumeric
        characters.

        For Azure DevOps repositories, it will use org/openhands-config/openhands-config
        format to match Azure DevOps's three-part repository structure (org/project/repo).

        Args:
            selected_repository: The repository path (e.g., "github.com/acme-co/api")

        Returns:
            A list of loaded microagents from the org/user level repository
        """
        loaded_microagents: list[BaseMicroagent] = []

        self.log(
            'debug',
            f'Starting org-level microagent loading for repository: {selected_repository}',
        )

        repo_parts = selected_repository.split('/')

        if len(repo_parts) < 2:
            self.log(
                'warning',
                f'Repository path has insufficient parts ({len(repo_parts)} < 2), skipping org-level microagents',
            )
            return loaded_microagents

        # Determine repository type
        is_azure_devops = self._is_azure_devops_repository(selected_repository)
        is_gitlab = self._is_gitlab_repository(selected_repository)

        # Extract the org/user name
        # Azure DevOps format: org/project/repo (3 parts) - extract org (first part)
        # GitHub/GitLab/Bitbucket format: owner/repo (2 parts) - extract owner (first part)
        if is_azure_devops and len(repo_parts) >= 3:
            org_name = repo_parts[0]  # Get org from org/project/repo
        else:
            org_name = repo_parts[-2]  # Get owner from owner/repo

        self.log(
            'info',
            f'Extracted org/user name: {org_name}',
        )
        self.log(
            'debug',
            f'Repository type detection - is_gitlab: {is_gitlab}, is_azure_devops: {is_azure_devops}',
        )

        # For GitLab and Azure DevOps, use openhands-config (since .openhands is not a valid repo name)
        # For other providers, use .openhands
        if is_gitlab:
            org_openhands_repo = f'{org_name}/openhands-config'
        elif is_azure_devops:
            # Azure DevOps format: org/project/repo
            # For org-level config, use: org/openhands-config/openhands-config
            org_openhands_repo = f'{org_name}/openhands-config/openhands-config'
        else:
            org_openhands_repo = f'{org_name}/.openhands'

        self.log(
            'info',
            f'Checking for org-level microagents at {org_openhands_repo}',
        )

        # Try to clone the org-level repo
        try:
            # Create a temporary directory for the org-level repo
            org_repo_dir = self.workspace_root / f'org_openhands_{org_name}'
            self.log(
                'debug',
                f'Creating temporary directory for org repo: {org_repo_dir}',
            )

            # Get authenticated URL and do a shallow clone (--depth 1) for efficiency
            try:
                remote_url = call_async_from_sync(
                    self.provider_handler.get_authenticated_git_url,
                    GENERAL_TIMEOUT,
                    org_openhands_repo,
                    is_optional=True,
                )
            except AuthenticationError as e:
                self.log(
                    'debug',
                    f'org-level microagent directory {org_openhands_repo} not found: {str(e)}',
                )
                raise
            except Exception as e:
                self.log(
                    'debug',
                    f'Failed to get authenticated URL for {org_openhands_repo}: {str(e)}',
                )
                raise

            clone_cmd = (
                f'GIT_TERMINAL_PROMPT=0 git clone --depth 1 {remote_url} {org_repo_dir}'
            )
            self.log(
                'info',
                'Executing clone command for org-level repo',
            )

            action = CmdRunAction(command=clone_cmd)
            obs = self.run_action(action)

            if isinstance(obs, CmdOutputObservation) and obs.exit_code == 0:
                self.log(
                    'info',
                    f'Successfully cloned org-level microagents from {org_openhands_repo}',
                )

                # Load microagents from the org-level repo
                org_microagents_dir = org_repo_dir / 'microagents'
                self.log(
                    'info',
                    f'Looking for microagents in directory: {org_microagents_dir}',
                )

                loaded_microagents = self._load_microagents_from_directory(
                    org_microagents_dir, 'org-level'
                )

                self.log(
                    'info',
                    f'Loaded {len(loaded_microagents)} microagents from org-level repository {org_openhands_repo}',
                )

                # Clean up the org repo directory
                action = CmdRunAction(f'rm -rf {org_repo_dir}')
                self.run_action(action)
            else:
                clone_error_msg = (
                    obs.content
                    if isinstance(obs, CmdOutputObservation)
                    else 'Unknown error'
                )
                exit_code = (
                    obs.exit_code if isinstance(obs, CmdOutputObservation) else 'N/A'
                )
                self.log(
                    'info',
                    f'No org-level microagents found at {org_openhands_repo} (exit_code: {exit_code})',
                )
                self.log(
                    'debug',
                    f'Clone command output: {clone_error_msg}',
                )

        except AuthenticationError as e:
            self.log(
                'debug',
                f'org-level microagent directory {org_openhands_repo} not found: {str(e)}',
            )
        except Exception as e:
            self.log(
                'debug',
                f'Error loading org-level microagents from {org_openhands_repo}: {str(e)}',
            )

        return loaded_microagents