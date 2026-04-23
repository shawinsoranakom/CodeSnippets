def _validate_repository_update(
        self,
        request: AppConversationUpdateRequest,
        existing_branch: str | None = None,
    ) -> None:
        """Validate repository-related fields in the update request.

        Args:
            request: The update request containing fields to validate
            existing_branch: The conversation's current branch (if any)

        Raises:
            ValueError: If validation fails
        """
        # Check if repository is being set
        if 'selected_repository' in request.model_fields_set:
            repo = request.selected_repository
            if repo is not None:
                # Validate repository format (owner/repo)
                if '/' not in repo or repo.count('/') != 1:
                    raise ValueError(
                        f"Invalid repository format: '{repo}'. Expected 'owner/repo'."
                    )

                # Sanitize: check for dangerous characters
                if any(c in repo for c in [';', '&', '|', '$', '`', '\n', '\r']):
                    raise ValueError(f"Invalid characters in repository name: '{repo}'")

                # If setting a repository, branch should also be provided
                # (either in this request or already exists in conversation)
                if (
                    'selected_branch' not in request.model_fields_set
                    and existing_branch is None
                ):
                    _logger.warning(
                        f'Repository {repo} set without branch in the same request '
                        'and no existing branch in conversation'
                    )
            else:
                # Repository is being removed (set to null)
                # Enforce consistency: branch and provider must also be cleared
                if 'selected_branch' in request.model_fields_set:
                    if request.selected_branch is not None:
                        raise ValueError(
                            'When removing repository, branch must also be cleared'
                        )
                if 'git_provider' in request.model_fields_set:
                    if request.git_provider is not None:
                        raise ValueError(
                            'When removing repository, git_provider must also be cleared'
                        )

        # Validate branch if provided
        if 'selected_branch' in request.model_fields_set:
            branch = request.selected_branch
            if branch is not None:
                ensure_valid_git_branch_name(branch)