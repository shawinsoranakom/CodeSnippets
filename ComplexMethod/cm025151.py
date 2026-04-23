async def resolve_dependencies_impl(itg: Integration) -> set[str]:
        domain = itg.domain

        # If it's already resolved, no point doing it again.
        if (result := resolved.get(itg)) is not None:
            if isinstance(result, Exception):
                raise result
            return result

        # If we are already resolving it, we have a circular dependency.
        if domain in resolving:
            if ignore_exceptions:
                resolved[itg] = set()
                return set()
            exc = CircularDependency([domain])
            resolved[itg] = exc
            raise exc

        resolving.add(domain)

        dependencies_domains = set(itg.dependencies)
        if possible_after_dependencies is not UNDEFINED:
            if possible_after_dependencies is None:
                after_dependencies: Iterable[str] = itg.after_dependencies
            else:
                after_dependencies = (
                    set(itg.after_dependencies) & possible_after_dependencies
                )
            dependencies_domains.update(after_dependencies)
        dependencies = await async_get_integrations(itg.hass, dependencies_domains)

        all_dependencies: set[str] = set()
        for dep_domain, dep_integration in dependencies.items():
            if isinstance(dep_integration, Exception):
                if ignore_exceptions:
                    continue
                resolved[itg] = dep_integration
                raise dep_integration

            all_dependencies.add(dep_domain)

            try:
                dep_dependencies = await resolve_dependencies_impl(dep_integration)
            except CircularDependency as exc:
                exc.extend_cycle(domain)
                resolved[itg] = exc
                raise
            except Exception as exc:
                resolved[itg] = exc
                raise

            all_dependencies.update(dep_dependencies)

        resolving.remove(domain)

        resolved[itg] = all_dependencies
        return all_dependencies