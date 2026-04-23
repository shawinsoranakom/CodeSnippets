async def _async_process_integration(
        self, integration: Integration, done: set[str]
    ) -> None:
        """Process an integration and requirements."""
        if integration.requirements:
            await self.async_process_requirements(
                integration.domain, integration.requirements, integration.is_built_in
            )

        cache = self.integrations_with_reqs

        deps_to_check = {
            dep
            for dep in integration.dependencies + integration.after_dependencies
            if dep not in done
            # If the dep is in the cache and it's an Integration
            # it's already been checked for the requirements and we should
            # not check it again.
            and (
                not (cached_integration := cache.get(dep))
                or type(cached_integration) is not Integration
            )
        }

        for check_domain, to_check in DISCOVERY_INTEGRATIONS.items():
            if (
                check_domain not in done
                and check_domain not in deps_to_check
                # If the integration is in the cache and it's an Integration
                # it's already been checked for the requirements and we should
                # not check it again.
                and (
                    not (cached_integration := cache.get(check_domain))
                    or type(cached_integration) is not Integration
                )
                and any(check in integration.manifest for check in to_check)
            ):
                deps_to_check.add(check_domain)

        if not deps_to_check:
            return

        exceptions: list[Exception] = []
        # We don't create tasks here since everything waits for the pip lock
        # anyways and we want to make sure we don't start a bunch of tasks
        # that will just wait for the lock.
        for dep in deps_to_check:
            # We want all the async_get_integration_with_requirements calls to
            # happen even if one fails. So we catch the exception and store it
            # to raise the first one after all are done to behave like asyncio
            # gather.
            try:
                await self.async_get_integration_with_requirements(dep, done)
            except IntegrationNotFound as ex:
                if (
                    integration.is_built_in
                    or ex.domain not in integration.after_dependencies
                ):
                    exceptions.append(ex)
            except Exception as ex:  # noqa: BLE001
                exceptions.insert(0, ex)

        if exceptions:
            raise exceptions[0]