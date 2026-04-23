def filter_targets[TCompletionTarget: CompletionTarget](
    targets: c.Iterable[TCompletionTarget],
    patterns: list[str],
    include: bool = True,
    errors: bool = True,
) -> c.Iterable[TCompletionTarget]:
    """Iterate over the given targets and filter them based on the supplied arguments."""
    unmatched = set(patterns or ())
    compiled_patterns = dict((p, re.compile('^%s$' % p)) for p in patterns) if patterns else None

    for target in targets:
        matched_directories = set()
        match = False

        if patterns:
            for alias in target.aliases:
                for pattern in patterns:
                    if compiled_patterns[pattern].match(alias):
                        match = True

                        try:
                            unmatched.remove(pattern)
                        except KeyError:
                            pass

                        if alias.endswith('/'):
                            if target.base_path and len(target.base_path) > len(alias):
                                matched_directories.add(target.base_path)
                            else:
                                matched_directories.add(alias)
        elif include:
            match = True
            if not target.base_path:
                matched_directories.add('.')
            for alias in target.aliases:
                if alias.endswith('/'):
                    if target.base_path and len(target.base_path) > len(alias):
                        matched_directories.add(target.base_path)
                    else:
                        matched_directories.add(alias)

        if match != include:
            continue

        yield target

    if errors:
        if unmatched:
            raise TargetPatternsNotMatched(unmatched)