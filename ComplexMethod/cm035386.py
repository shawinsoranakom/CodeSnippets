async def verify_repo_provider(
        self,
        repository: str,
        specified_provider: ProviderType | None = None,
        is_optional: bool = False,
    ) -> Repository:
        errors = []

        if specified_provider:
            try:
                service = self.get_service(specified_provider)
                return await service.get_repository_details_from_repo_name(repository)
            except Exception as e:
                errors.append(f'{specified_provider.value}: {str(e)}')

        for provider in self.provider_tokens:
            try:
                service = self.get_service(provider)
                return await service.get_repository_details_from_repo_name(repository)
            except Exception as e:
                errors.append(f'{provider.value}: {str(e)}')

        # Log detailed error based on whether we had tokens or not
        # For optional repositories (like org-level microagents), use debug level
        log_fn = logger.debug if is_optional else logger.error

        if not self.provider_tokens:
            log_fn(
                f'Failed to access repository {repository}: No provider tokens available. '
                f'provider_tokens dict is empty.'
            )
        elif errors:
            log_fn(
                f'Failed to access repository {repository} with all available providers. '
                f'Tried providers: {list(self.provider_tokens.keys())}. '
                f'Errors: {"; ".join(errors)}'
            )
        else:
            log_fn(
                f'Failed to access repository {repository}: Unknown error (no providers tried, no errors recorded)'
            )
        raise AuthenticationError(f'Unable to access repo {repository}')