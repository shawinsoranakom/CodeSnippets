def _load_manifest(module: str, manifest_content: dict) -> dict:
    """ Load and validate the module manifest.

    Return a new dictionary with cleaned and validated keys.
    """

    manifest = copy.deepcopy(_DEFAULT_MANIFEST)
    manifest.update(manifest_content)

    if not manifest.get('author'):
        # Altought contributors and maintainer are not documented, it is
        # not uncommon to find them in manifest files, use them as
        # alternative.
        author = manifest.get('contributors') or manifest.get('maintainer') or ''
        manifest['author'] = str(author)
        _logger.warning("Missing `author` key in manifest for %r, defaulting to %r", module, str(author))

    if not manifest.get('license'):
        manifest['license'] = 'LGPL-3'
        _logger.warning("Missing `license` key in manifest for %r, defaulting to LGPL-3", module)

    if module == 'base':
        manifest['depends'] = []
    elif not manifest['depends']:
        # prevent the hack `'depends': []` except 'base' module
        manifest['depends'] = ['base']

    depends = manifest['depends']
    assert isinstance(depends, Collection)

    # auto_install is either `False` (by default) in which case the module
    # is opt-in, either a list of dependencies in which case the module is
    # automatically installed if all dependencies are (special case: [] to
    # always install the module), either `True` to auto-install the module
    # in case all dependencies declared in `depends` are installed.
    if isinstance(manifest['auto_install'], Iterable):
        manifest['auto_install'] = auto_install_set = set(manifest['auto_install'])
        non_dependencies = auto_install_set.difference(depends)
        assert not non_dependencies, (
            "auto_install triggers must be dependencies,"
            f" found non-dependencies [{', '.join(non_dependencies)}] for module {module}"
        )
    elif manifest['auto_install']:
        manifest['auto_install'] = set(depends)

    try:
        manifest['version'] = adapt_version(str(manifest['version']))
    except ValueError as e:
        if manifest['installable']:
            raise ValueError(f"Module {module}: invalid manifest") from e
    if manifest['installable'] and not check_version(str(manifest['version']), should_raise=False):
        _logger.warning("The module %s has an incompatible version, setting installable=False", module)
        manifest['installable'] = False

    return manifest