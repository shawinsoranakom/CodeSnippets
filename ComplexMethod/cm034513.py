def main():
    module = AnsibleModule(
        argument_spec={
            'allow_downgrade_to_insecure': {
                'type': 'bool',
            },
            'allow_insecure': {
                'type': 'bool',
            },
            'allow_weak': {
                'type': 'bool',
            },
            'architectures': {
                'elements': 'str',
                'type': 'list',
            },
            'by_hash': {
                'type': 'bool',
            },
            'check_date': {
                'type': 'bool',
            },
            'check_valid_until': {
                'type': 'bool',
            },
            'components': {
                'elements': 'str',
                'type': 'list',
            },
            'date_max_future': {
                'type': 'int',
            },
            'enabled': {
                'type': 'bool',
            },
            'exclude': {
                'elements': 'str',
                'type': 'list',
            },
            'include': {
                'elements': 'str',
                'type': 'list',
            },
            'inrelease_path': {
                'type': 'str',
            },
            'install_python_debian': {
                'type': 'bool',
                'default': False,
            },
            'languages': {
                'elements': 'str',
                'type': 'list',
            },
            'name': {
                'type': 'str',
                'required': True,
            },
            'pdiffs': {
                'type': 'bool',
            },
            'signed_by': {
                'type': 'str',
            },
            'suites': {
                'elements': 'str',
                'type': 'list',
            },
            'targets': {
                'elements': 'str',
                'type': 'list',
            },
            'trusted': {
                'type': 'bool',
            },
            'types': {
                'choices': [
                    'deb',
                    'deb-src',
                ],
                'elements': 'str',
                'type': 'list',
                'default': [
                    'deb',
                ]
            },
            'uris': {
                'elements': 'str',
                'type': 'list',
            },
            # non-deb822 args
            'mode': {
                'type': 'raw',
                'default': '0644',
            },
            'state': {
                'type': 'str',
                'choices': [
                    'present',
                    'absent',
                ],
                'default': 'present',
            },
        },
        mutually_exclusive=[
            ['exclude', 'include']
        ],
        supports_check_mode=True,
    )

    if not HAS_DEBIAN:
        deb_pkg_name = 'python3-debian'
        # This interpreter can't see the debian Python library- we'll do the following to try and fix that as per
        # the apt_repository module:
        # 1) look in common locations for system-owned interpreters that can see it; if we find one, respawn under it
        # 2) finding none, try to install a matching python-debian package for the current interpreter version;
        #    we limit to the current interpreter version to try and avoid installing a whole other Python just
        #    for deb support
        # 3) if we installed a support package, try to respawn under what we think is the right interpreter (could be
        #    the current interpreter again, but we'll let it respawn anyway for simplicity)
        # 4) if still not working, return an error and give up (some corner cases not covered, but this shouldn't be
        #    made any more complex than it already is to try and cover more, eg, custom interpreters taking over
        #    system locations)

        if has_respawned():
            # this shouldn't be possible; short-circuit early if it happens...
            module.fail_json(msg=f"{deb_pkg_name} must be installed and visible from {sys.executable}.")

        interpreters = ['/usr/bin/python3', '/usr/bin/python']

        interpreter = probe_interpreters_for_module(interpreters, 'debian')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed

        # don't make changes if we're in check_mode
        if module.check_mode:
            module.fail_json(msg=f"{deb_pkg_name} must be installed to use check mode. If run with install_python_debian, this module can auto-install it.")

        if module.params['install_python_debian']:
            install_python_debian(module, deb_pkg_name)
        else:
            module.fail_json(msg=f'{deb_pkg_name} is not installed, and install_python_debian is False')

        # try again to find the bindings in common places
        interpreter = probe_interpreters_for_module(interpreters, 'debian')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            # NB: respawn is somewhat wasteful if it's this interpreter, but simplifies the code
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed
        else:
            # we've done all we can do; just tell the user it's busted and get out
            module.fail_json(msg=missing_required_lib(deb_pkg_name),
                             exception=DEBIAN_IMP_ERR)

    check_mode = module.check_mode

    changed = False

    # Make a copy, so we don't mutate module.params to avoid future issues
    params = module.params.copy()

    # popped non-deb822 args
    mode = params.pop('mode')
    state = params.pop('state')
    params.pop('install_python_debian')

    name = params['name']
    # Generate legacy-normalized slug for backward compatibility check
    legacy_slug = re.sub(
        r'[^a-z0-9-]+',
        '',
        re.sub(r'[_\s]+', '-', name.lower()),
    )
    legacy_sources = make_sources_filename(legacy_slug)

    if os.path.exists(legacy_sources):
        # Legacy file exists, reuse the old naming to maintain consistency
        slug = legacy_slug
    else:
        # No legacy file, use the new naming convention
        slug = name.replace(' ', '-')
    sources_filename = make_sources_filename(slug)

    if state == 'absent':
        if os.path.exists(sources_filename):
            if not check_mode:
                os.unlink(sources_filename)
            changed |= True
        for ext in ('asc', 'gpg'):
            signed_by_filename = make_signed_by_filename(slug, ext)
            if os.path.exists(signed_by_filename):
                if not check_mode:
                    os.unlink(signed_by_filename)
                changed = True
        module.exit_json(
            repo=None,
            changed=changed,
            dest=sources_filename,
            key_filename=signed_by_filename,
        )

    deb822 = Deb822()
    signed_by_filename = None
    for key, value in sorted(params.items()):
        if value is None:
            continue

        if isinstance(value, bool):
            value = format_bool(value)
        elif isinstance(value, int):
            value = to_native(value)
        elif is_sequence(value):
            value = format_list(value)
        elif key == 'signed_by':
            key_changed, signed_by_filename, signed_by_data = write_signed_by_key(module, value, slug)
            value = signed_by_filename or signed_by_data
            changed |= key_changed

        if value.count('\n') > 0:
            value = format_multiline(value)

        deb822[format_field_name(key)] = value

    repo = deb822.dump()
    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'wb') as f:
        f.write(to_bytes(repo))

    sources_filename = make_sources_filename(slug)

    src_chksum = module.sha256(tmpfile)
    dest_chksum = module.sha256(sources_filename)

    if src_chksum != dest_chksum:
        if not check_mode:
            module.atomic_move(tmpfile, sources_filename)
        changed |= True

    changed |= module.set_mode_if_different(sources_filename, mode, False)

    module.exit_json(
        repo=repo,
        changed=changed,
        dest=sources_filename,
        key_filename=signed_by_filename,
    )