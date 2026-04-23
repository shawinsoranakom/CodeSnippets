def recursive_finder(
    name: str,
    module_fqn: str,
    module_data: bytes,
    zf: zipfile.ZipFile,
    date_time: datetime.datetime,
    extension_manager: _builder.ExtensionManager,
) -> ModuleMetadata:
    """
    Using ModuleDepFinder, make sure we have all of the module_utils files that
    the module and its module_utils files needs. (no longer actually recursive)
    :arg name: Name of the python module we're examining
    :arg module_fqn: Fully qualified name of the python module we're scanning
    :arg module_data: string Python code of the module we're scanning
    :arg zf: An open :python:class:`zipfile.ZipFile` object that holds the Ansible module payload
        which we're assembling
    """
    # py_module_cache maps python module names to a tuple of the code in the module
    # and the pathname to the module.
    # Here we pre-load it with modules which we create without bothering to
    # read from actual files (In some cases, these need to differ from what ansible
    # ships because they're namespace packages in the module)
    # FIXME: do we actually want ns pkg behavior for these? Seems like they should just be forced to emptyish pkg stubs
    py_module_cache = {
        ('ansible',): (
            b'from pkgutil import extend_path\n'
            b'__path__=extend_path(__path__,__name__)\n'
            b'__version__="' + to_bytes(__version__) +
            b'"\n__author__="' + to_bytes(__author__) + b'"\n',
            'ansible/__init__.py'),
        ('ansible', 'module_utils'): (
            b'from pkgutil import extend_path\n'
            b'__path__=extend_path(__path__,__name__)\n',
            'ansible/module_utils/__init__.py')}

    module_utils_paths = [p for p in module_utils_loader._get_paths(subdirs=False) if os.path.isdir(p)]
    module_utils_paths.append(_MODULE_UTILS_PATH)

    finder = ModuleDepFinder(module_fqn, module_data)
    module_metadata = _get_module_metadata(finder.tree)

    embeds = finder.embeds.copy()

    if not isinstance(module_metadata, ModuleMetadataV1):
        raise NotImplementedError()

    profile = module_metadata.serialization_profile

    # the format of this set is a tuple of the module name and whether the import is ambiguous as a module name
    # or an attribute of a module (e.g. from x.y import z <-- is z a module or an attribute of x.y?)
    modules_to_process = [_ModuleUtilsProcessEntry(m, True, False, is_optional=m in finder.optional_imports) for m in finder.submodules]

    # include module_utils that are always required
    modules_to_process.extend((
        _ModuleUtilsProcessEntry.from_module(_loader),
        _ModuleUtilsProcessEntry.from_module(_basic),
        _ModuleUtilsProcessEntry.from_module_name(_json.get_module_serialization_profile_module_name(profile, True)),
        _ModuleUtilsProcessEntry.from_module_name(_json.get_module_serialization_profile_module_name(profile, False)),
    ))

    modules_to_process.extend(_ModuleUtilsProcessEntry.from_module_name(name) for name in extension_manager.module_names)

    module_info: ModuleUtilLocatorBase

    # we'll be adding new modules inline as we discover them, so just keep going til we've processed them all
    while modules_to_process:
        modules_to_process.sort()  # not strictly necessary, but nice to process things in predictable and repeatable order
        entry = modules_to_process.pop(0)

        if entry.name_parts in py_module_cache:
            # this is normal; we'll often see the same module imported many times, but we only need to process it once
            continue

        if entry.name_parts[0:2] == ('ansible', 'module_utils'):
            module_info = LegacyModuleUtilLocator(entry.name_parts, is_ambiguous=entry.is_ambiguous,
                                                  mu_paths=module_utils_paths, child_is_redirected=entry.child_is_redirected)
        elif entry.name_parts[0] == 'ansible_collections':
            module_info = CollectionModuleUtilLocator(entry.name_parts, is_ambiguous=entry.is_ambiguous,
                                                      child_is_redirected=entry.child_is_redirected, is_optional=entry.is_optional)
        else:
            # FIXME: dot-joined result
            display.warning('ModuleDepFinder improperly found a non-module_utils import %s'
                            % [entry.name_parts])
            continue

        # Could not find the module.  Construct a helpful error message.
        if not module_info.found:
            if entry.is_optional:
                # this was a best-effort optional import that we couldn't find, oh well, move along...
                continue
            # FIXME: use dot-joined candidate names
            msg = 'Could not find imported module support code for {0}. Looked for ({1})'.format(module_fqn, module_info.candidate_names_joined)
            raise AnsibleError(msg)

        # check the cache one more time with the module we actually found, since the name could be different than the input
        # eg, imported name vs module
        if module_info.fq_name_parts in py_module_cache:
            continue

        finder = ModuleDepFinder('.'.join(module_info.fq_name_parts), module_info.source_code, is_pkg_init=module_info.is_package)
        embeds.update(finder.embeds)
        modules_to_process.extend(_ModuleUtilsProcessEntry(m, True, False, is_optional=m in finder.optional_imports)
                                  for m in finder.submodules if m not in py_module_cache)

        # we've processed this item, add it to the output list
        py_module_cache[module_info.fq_name_parts] = (module_info.source_code, module_info.output_path)

        # ensure we process all ancestor package inits
        accumulated_pkg_name = []
        for pkg in module_info.fq_name_parts[:-1]:
            accumulated_pkg_name.append(pkg)  # we're accumulating this across iterations
            normalized_name = tuple(accumulated_pkg_name)  # extra machinations to get a hashable type (list is not)
            if normalized_name not in py_module_cache:
                modules_to_process.append(_ModuleUtilsProcessEntry(normalized_name, False, module_info.redirected, is_optional=entry.is_optional))

    written_files = set()
    for py_module_name in py_module_cache:
        source_code, py_module_file_name = py_module_cache[py_module_name]

        mu_file = to_text(py_module_file_name, errors='surrogate_or_strict')
        display.vvvvv("Including module_utils file %s" % mu_file)

        zf.writestr(_make_zinfo(py_module_file_name, date_time, zf=zf), source_code)
        written_files.add(py_module_file_name)

        if extension_manager.debugger_enabled and (origin := Origin.get_tag(source_code)) and origin.path:
            extension_manager.source_mapping[origin.path] = py_module_file_name

    anchor_cache: dict[str, pathlib.Path] = {}
    for embed in embeds:
        try:
            embed_path_cm = embed.path_context_manager
        except ModuleNotFoundError as e:
            # the source exception message includes the package name, no need to repeat
            raise AnsibleError('Embed package not found while packaging module.', obj=embed.package) from e

        with embed_path_cm as path:
            if not path.is_file():
                raise AnsibleError(f'Embed resource {embed.resource!r} not found while packaging module.', obj=embed.resource)
            anchor_parts = embed.package.split('.')
            if anchor_parts[0] == 'ansible':
                try:
                    root = anchor_cache['ansible']
                except KeyError:
                    root = anchor_cache['ansible'] = ir_files('ansible').parent
                rel_path = path.relative_to(root)
            elif anchor_parts[0] == 'ansible_collections':
                pkg = '.'.join(anchor_parts[:3])
                try:
                    root = anchor_cache[pkg]
                except KeyError:
                    root = anchor_cache[pkg] = ir_files(pkg).parents[2]
                rel_path = path.relative_to(root)
            else:
                raise AnsibleError('Embed must be an ansible/ansible_collections resource.', obj=embed.resource)

            display.vvvvv(f"Including embed file {rel_path}")
            zf.writestr(_make_zinfo(str_path := str(rel_path), date_time, zf=zf), path.read_bytes())
            written_files.add(str_path)
            for parent in rel_path.parents:
                if not parent.name:
                    continue
                p_init = str(parent / '__init__.py')
                if p_init not in written_files:
                    display.vvvvv(f"Including parent init file {p_init}")
                    zf.writestr(_make_zinfo(p_init, date_time, zf=zf), b'')
                    written_files.add(p_init)

    return module_metadata