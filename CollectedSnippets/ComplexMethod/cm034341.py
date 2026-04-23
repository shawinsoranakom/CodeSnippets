def _build_files_manifest_distlib(b_collection_path, namespace, name, manifest_control,
                                  license_file):
    # type: (bytes, str, str, dict[str, t.Any], t.Optional[str]) -> FilesManifestType
    if not HAS_DISTLIB:
        raise AnsibleError('Use of "manifest" requires the python "distlib" library')

    if manifest_control is None:
        manifest_control = {}

    try:
        control = ManifestControl(**manifest_control)
    except TypeError as ex:
        raise AnsibleError(f'Invalid "manifest" provided: {ex}')

    if not is_sequence(control.directives):
        raise AnsibleError(f'"manifest.directives" must be a list, got: {control.directives.__class__.__name__}')

    if not isinstance(control.omit_default_directives, bool):
        raise AnsibleError(
            '"manifest.omit_default_directives" is expected to be a boolean, got: '
            f'{control.omit_default_directives.__class__.__name__}'
        )

    if control.omit_default_directives and not control.directives:
        raise AnsibleError(
            '"manifest.omit_default_directives" was set to True, but no directives were defined '
            'in "manifest.directives". This would produce an empty collection artifact.'
        )

    directives = []
    if control.omit_default_directives:
        directives.extend(control.directives)
    else:
        directives.extend([
            'include meta/*.yml',
            'include *.txt *.md *.rst *.license COPYING LICENSE',
            'recursive-include .reuse **',
            'recursive-include LICENSES **',
            'recursive-include tests **',
            'recursive-include docs **.rst **.yml **.yaml **.json **.j2 **.txt **.license',
            'recursive-include roles **.yml **.yaml **.json **.j2 **.license',
            'recursive-include playbooks **.yml **.yaml **.json **.license',
            'recursive-include changelogs **.yml **.yaml **.license',
            'recursive-include plugins */**.py */**.license',
        ])

        if license_file:
            directives.append(f'include {license_file}')

        plugins = set(l.package.split('.')[-1] for d, l in get_all_plugin_loaders())
        for plugin in sorted(plugins):
            if plugin in ('modules', 'module_utils'):
                continue
            elif plugin in C.DOCUMENTABLE_PLUGINS:
                directives.append(
                    f'recursive-include plugins/{plugin} **.yml **.yaml'
                )

        directives.extend([
            'recursive-include plugins/modules **.ps1 **.yml **.yaml **.license',
            'recursive-include plugins/module_utils **.ps1 **.psm1 **.cs **.license',
        ])

        directives.extend(control.directives)

        directives.extend([
            f'exclude galaxy.yml galaxy.yaml MANIFEST.json FILES.json {namespace}-{name}-*.tar.gz',
            'recursive-exclude tests/output **',
            'global-exclude /.* /__pycache__ *.pyc *.pyo *.bak *~ *.swp',
        ])

    display.vvv('Manifest Directives:')
    display.vvv(textwrap.indent('\n'.join(directives), '    '))

    u_collection_path = to_text(b_collection_path, errors='surrogate_or_strict')
    m = Manifest(u_collection_path)
    for directive in directives:
        try:
            m.process_directive(directive)
        except DistlibException as e:
            raise AnsibleError(f'Invalid manifest directive: {e}')
        except Exception as e:
            raise AnsibleError(f'Unknown error processing manifest directive: {e}')

    manifest = _make_manifest()

    for abs_path in m.sorted(wantdirs=True):
        rel_path = os.path.relpath(abs_path, u_collection_path)
        if os.path.isdir(abs_path):
            manifest_entry = _make_entry(rel_path, 'dir')
        else:
            manifest_entry = _make_entry(
                rel_path,
                'file',
                chksum_type='sha256',
                chksum=secure_hash(abs_path, hash_func=sha256)
            )

        manifest['files'].append(manifest_entry)
    return manifest