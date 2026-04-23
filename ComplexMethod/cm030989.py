def format_resources(use_resources: dict[str, str | None]) -> str:
    all_resources = set(ALL_RESOURCES)

    values = []
    for name in sorted(use_resources):
        if use_resources[name] is not None:
            values.append(f'{name}={use_resources[name]}')

    # Express resources relative to "all"
    relative_all = ['all']
    for name in sorted(all_resources - set(use_resources)):
        relative_all.append(f'-{name}')
    for name in sorted(set(use_resources) - all_resources):
        if use_resources[name] is None:
            relative_all.append(name)
    all_text = ','.join(relative_all + values)
    all_text = f"resources: {all_text}"

    # List of enabled resources
    resources = []
    for name in sorted(use_resources):
        if use_resources[name] is None:
            resources.append(name)
    text = ','.join(resources + values)
    text = f"resources ({len(use_resources)}): {text}"

    # Pick the shortest string (prefer relative to all if lengths are equal)
    if len(all_text) <= len(text):
        return all_text
    else:
        return text