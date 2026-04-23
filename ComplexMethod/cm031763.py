def get_identifiers_and_strings() -> 'tuple[set[str], dict[str, str]]':
    identifiers = set(IDENTIFIERS)
    strings = {}
    # Note that we store strings as they appear in C source, so the checks here
    # can be defeated, e.g.:
    # - "a" and "\0x61" won't be reported as duplicate.
    # - "\n" appears as 2 characters.
    # Probably not worth adding a C string parser.
    for name, string, *_ in iter_global_strings():
        if string is None:
            if name not in IGNORED:
                identifiers.add(name)
        else:
            if len(string) == 1 and ord(string) < 256:
                # Give a nice message for common mistakes.
                # To cover tricky cases (like "\n") we also generate C asserts.
                raise ValueError(
                    'do not use &_Py_ID or &_Py_STR for one-character latin-1 '
                    f'strings, use _Py_LATIN1_CHR instead: {string!r}')
            if string not in strings:
                strings[string] = name
            elif name != strings[string]:
                raise ValueError(f'name mismatch for string {string!r} ({name!r} != {strings[string]!r}')
    overlap = identifiers & set(strings.keys())
    if overlap:
        raise ValueError(
            'do not use both _Py_ID and _Py_DECLARE_STR for the same string: '
            + repr(overlap))
    return identifiers, strings