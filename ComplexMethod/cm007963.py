def parse_dependency(line: str, *, require_version: bool = False) -> Dependency:
    # Ref: https://packaging.python.org/en/latest/specifications/name-normalization/
    NAME_RE = re.compile(r'^(?P<name>[A-Z0-9](?:[A-Z0-9._-]*[A-Z0-9])?)', re.IGNORECASE)

    line = line.rstrip().removesuffix('\\')
    mobj = NAME_RE.match(line)
    if not mobj:
        raise ValueError(f'unable to parse Dependency.name from line:\n    {line}')

    name = mobj.group('name')
    rest = line[len(name):].lstrip()
    specifier_or_direct_reference, _, markers = map(str.strip, rest.partition(';'))
    specifier, _, direct_reference = map(str.strip, specifier_or_direct_reference.partition('@'))

    exact_version = None
    if ',' not in specifier and specifier.startswith('=='):
        exact_version = specifier[2:]

    # Ref: https://packaging.python.org/en/latest/specifications/binary-distribution-format/
    if direct_reference and not exact_version:
        filename = urllib.parse.urlparse(direct_reference).path.rpartition('/')[2]
        if filename.endswith(('.tar.gz', '.whl')):
            exact_version = parse_version_from_dist(filename, name)

    if require_version and not exact_version:
        raise ValueError(f'unable to parse Dependency.exact_version from line:\n    {line}')

    return Dependency(
        name=name,
        exact_version=exact_version,
        direct_reference=direct_reference or None,
        specifier=specifier or None,
        markers=markers or None)