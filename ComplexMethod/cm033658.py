def walk_completion_targets(targets: c.Iterable[CompletionTarget], prefix: str, short: bool = False) -> tuple[str, ...]:
    """Return a tuple of targets from the given target iterable which match the given prefix."""
    aliases = set(alias for target in targets for alias in target.aliases)

    if prefix.endswith('/') and prefix in aliases:
        aliases.remove(prefix)

    matches = [alias for alias in aliases if alias.startswith(prefix) and '/' not in alias[len(prefix):-1]]

    if short:
        offset = len(os.path.dirname(prefix))
        if offset:
            offset += 1
            relative_matches = [match[offset:] for match in matches if len(match) > offset]
            if len(relative_matches) > 1:
                matches = relative_matches

    return tuple(sorted(matches))