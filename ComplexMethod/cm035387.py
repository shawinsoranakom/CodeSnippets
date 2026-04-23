async def get_authenticated_git_url(
        self, repo_name: str, is_optional: bool = False
    ) -> str:
        """Get an authenticated git URL for a repository.

        Args:
            repo_name: Repository name (owner/repo)
            is_optional: If True, logs at debug level instead of error level when repo not found

        Returns:
            Authenticated git URL if credentials are available, otherwise regular HTTPS URL
        """
        try:
            repository = await self.verify_repo_provider(
                repo_name, is_optional=is_optional
            )
        except AuthenticationError:
            raise Exception('Git provider authentication issue when getting remote URL')

        provider = repository.git_provider
        repo_name = repository.full_name

        domain = self.PROVIDER_DOMAINS.get(provider, '')

        # If provider tokens are provided, use the host from the token if available
        # Note: For Azure DevOps, don't use the host field as it may contain org/project path
        if self.provider_tokens and provider in self.provider_tokens:
            if provider != ProviderType.AZURE_DEVOPS:
                domain = self.provider_tokens[provider].host or domain

        # Detect protocol before normalizing domain
        # Default to https, but preserve http if explicitly specified
        protocol = 'https'
        if domain and domain.strip().startswith('http://'):
            # Check if insecure HTTP access is allowed
            allow_insecure = os.environ.get(
                'ALLOW_INSECURE_GIT_ACCESS', 'false'
            ).lower() in ('true', '1', 'yes')
            if not allow_insecure:
                raise ValueError(
                    'Attempting to connect to an insecure git repository over HTTP. '
                    "If you'd like to allow this nonetheless, set "
                    'ALLOW_INSECURE_GIT_ACCESS=true as an environment variable.'
                )
            protocol = 'http'

        # Normalize domain to prevent double protocols or path segments
        if domain:
            domain = domain.strip()
            domain = domain.replace('https://', '').replace('http://', '')
            # Remove any trailing path like /api/v3 or /api/v4
            if '/' in domain:
                domain = domain.split('/')[0]

        # Try to use token if available, otherwise use public URL
        if self.provider_tokens and provider in self.provider_tokens:
            git_token = self.provider_tokens[provider].token
            if git_token:
                token_value = git_token.get_secret_value()
                if provider == ProviderType.GITLAB:
                    remote_url = (
                        f'{protocol}://oauth2:{token_value}@{domain}/{repo_name}.git'
                    )
                elif provider == ProviderType.BITBUCKET:
                    # For Bitbucket, handle username:app_password format
                    if ':' in token_value:
                        # App token format: username:app_password
                        remote_url = (
                            f'{protocol}://{token_value}@{domain}/{repo_name}.git'
                        )
                    else:
                        # Access token format: use x-token-auth
                        remote_url = f'{protocol}://x-token-auth:{token_value}@{domain}/{repo_name}.git'
                elif provider == ProviderType.BITBUCKET_DATA_CENTER:
                    # DC uses HTTP Basic auth — token must be in username:token format
                    project, repo_slug = (
                        repo_name.split('/', 1)
                        if '/' in repo_name
                        else (repo_name, repo_name)
                    )
                    scm_path = f'scm/{project.lower()}/{repo_slug}.git'
                    # Percent-encode each credential part so special characters
                    # (e.g. @, #, /) don't break the URL.
                    if ':' in token_value:
                        dc_user, dc_pass = token_value.split(':', 1)
                        url_creds = (
                            f'{quote(dc_user, safe="")}:{quote(dc_pass, safe="")}'
                        )
                    else:
                        url_creds = f'x-token-auth:{quote(token_value, safe="")}'
                    remote_url = f'{protocol}://{url_creds}@{domain}/{scm_path}'
                elif provider == ProviderType.AZURE_DEVOPS:
                    # Azure DevOps uses PAT with Basic auth
                    # Format: https://{anything}:{PAT}@dev.azure.com/{org}/{project}/_git/{repo}
                    # The username can be anything (it's ignored), but cannot be empty
                    # We use the org name as the username for clarity
                    # repo_name is in format: org/project/repo
                    logger.info(
                        f'[Azure DevOps] Constructing authenticated git URL for repository: {repo_name}'
                    )
                    logger.debug(f'[Azure DevOps] Original domain: {domain}')
                    logger.debug(
                        f'[Azure DevOps] Token available: {bool(token_value)}, '
                        f'Token length: {len(token_value) if token_value else 0}'
                    )

                    # Remove domain prefix if it exists in domain variable
                    clean_domain = domain.replace('https://', '').replace('http://', '')
                    logger.debug(f'[Azure DevOps] Cleaned domain: {clean_domain}')

                    parts = repo_name.split('/')
                    logger.debug(
                        f'[Azure DevOps] Repository parts: {parts} (length: {len(parts)})'
                    )

                    if len(parts) >= 3:
                        org, project, repo = parts[0], parts[1], parts[2]
                        logger.info(
                            f'[Azure DevOps] Parsed repository - org: {org}, project: {project}, repo: {repo}'
                        )
                        # URL-encode org, project, and repo to handle spaces and special characters
                        org_encoded = quote(org, safe='')
                        project_encoded = quote(project, safe='')
                        repo_encoded = quote(repo, safe='')
                        logger.debug(
                            f'[Azure DevOps] URL-encoded parts - org: {org_encoded}, project: {project_encoded}, repo: {repo_encoded}'
                        )
                        # Use org name as username (it's ignored by Azure DevOps but required for git)
                        remote_url = f'https://{org}:***@{clean_domain}/{org_encoded}/{project_encoded}/_git/{repo_encoded}'
                        logger.info(
                            f'[Azure DevOps] Constructed git URL (token masked): {remote_url}'
                        )
                        # Set the actual URL with token
                        remote_url = f'https://{org}:{token_value}@{clean_domain}/{org_encoded}/{project_encoded}/_git/{repo_encoded}'
                    else:
                        # Fallback if format is unexpected
                        logger.warning(
                            f'[Azure DevOps] Unexpected repository format: {repo_name}. '
                            f'Expected org/project/repo (3 parts), got {len(parts)} parts. '
                            'Using fallback URL format.'
                        )
                        remote_url = (
                            f'https://user:{token_value}@{clean_domain}/{repo_name}.git'
                        )
                        logger.warning(
                            f'[Azure DevOps] Fallback URL constructed (token masked): '
                            f'https://user:***@{clean_domain}/{repo_name}.git'
                        )
                else:
                    # GitHub, Forgejo
                    remote_url = f'{protocol}://{token_value}@{domain}/{repo_name}.git'
            else:
                remote_url = f'{protocol}://{domain}/{repo_name}.git'
        else:
            remote_url = f'{protocol}://{domain}/{repo_name}.git'

        return remote_url