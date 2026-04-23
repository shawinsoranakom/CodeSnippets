def _check_circular_deps(
    integrations: dict[str, Integration],
    start_domain: str,
    integration: Integration,
    checked: set[str],
    checking: deque[str],
) -> None:
    """Check for circular dependencies pointing at starting_domain."""

    if integration.domain in checked or integration.domain in checking:
        return

    checking.append(integration.domain)
    for domain in integration.manifest.get("dependencies", []):
        if domain == start_domain:
            integrations[start_domain].add_error(
                "dependencies",
                f"Found a circular dependency with {integration.domain} ({', '.join(checking)})",
            )
            break

        _check_circular_deps(
            integrations, start_domain, integrations[domain], checked, checking
        )
    else:
        for domain in integration.manifest.get("after_dependencies", []):
            if domain == start_domain:
                integrations[start_domain].add_error(
                    "dependencies",
                    f"Found a circular dependency with after dependencies of {integration.domain} ({', '.join(checking)})",
                )
                break

            _check_circular_deps(
                integrations, start_domain, integrations[domain], checked, checking
            )
    checked.add(integration.domain)
    checking.remove(integration.domain)