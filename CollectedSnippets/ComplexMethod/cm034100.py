def _configure_base(base, config_dict):
    """Configure the dnf Base object. Returns list of warnings."""
    warnings = []
    conf = base.conf

    conf_file = config_dict.get('conf_file')
    if conf_file:
        if not os.access(conf_file, os.R_OK):
            raise _DnfScriptError(f'cannot read configuration file: {conf_file}')
        conf.config_file_path = conf_file

    conf.read()
    conf.debuglevel = 0

    disable_gpg_check = config_dict.get('disable_gpg_check', False)
    conf.gpgcheck = not disable_gpg_check
    conf.localpkg_gpgcheck = not disable_gpg_check
    conf.assumeyes = True

    sslverify = config_dict.get('sslverify', True)
    conf.sslverify = sslverify

    installroot = config_dict.get('installroot', '/')
    if not os.path.isdir(installroot):
        raise _DnfScriptError(f'Installroot {installroot} must be a directory')

    conf.installroot = installroot
    conf.substitutions.update_from_etc(installroot)

    exclude = config_dict.get('exclude', [])
    if exclude:
        _excludes = list(conf.exclude)
        _excludes.extend(exclude)
        conf.exclude = _excludes

    disable_excludes = config_dict.get('disable_excludes')
    if disable_excludes:
        _disable_excludes = list(conf.disable_excludes)
        if disable_excludes not in _disable_excludes:
            _disable_excludes.append(disable_excludes)
            conf.disable_excludes = _disable_excludes

    releasever = config_dict.get('releasever')
    if releasever is not None:
        conf.substitutions['releasever'] = releasever

    if conf.substitutions.get('releasever') is None:
        warnings.append('Unable to detect release version (use "releasever" option to specify release version)')
        conf.substitutions['releasever'] = ''

    for opt in ('cachedir', 'logdir', 'persistdir'):
        conf.prepend_installroot(opt)

    skip_broken = config_dict.get('skip_broken', False)
    if skip_broken:
        conf.strict = 0

    nobest = config_dict.get('nobest')
    best = config_dict.get('best')
    if nobest is not None:
        conf.best = not nobest
    elif best is not None:
        conf.best = best

    download_only = config_dict.get('download_only', False)
    if download_only:
        conf.downloadonly = True
        download_dir = config_dict.get('download_dir')
        if download_dir:
            conf.destdir = download_dir

    cacheonly = config_dict.get('cacheonly', False)
    if cacheonly:
        conf.cacheonly = True

    autoremove = config_dict.get('autoremove', False)
    conf.clean_requirements_on_remove = autoremove

    install_weak_deps = config_dict.get('install_weak_deps', True)
    conf.install_weak_deps = install_weak_deps

    return warnings