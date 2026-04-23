def exec_script(cr, installed_version, pyfile, addon, stage, version=None):
    version = version or installed_version
    name, ext = os.path.splitext(os.path.basename(pyfile))
    if ext.lower() != '.py':
        return
    try:
        mod = load_script(pyfile, name)
    except ImportError as e:
        raise ImportError('module %(addon)s: Unable to load %(stage)s-migration file %(file)s' % dict(locals(), file=pyfile)) from e

    if not hasattr(mod, 'migrate'):
        raise AttributeError(
            'module %(addon)s: Each %(stage)s-migration file must have a "migrate(cr, installed_version)" function, not found in %(file)s' % dict(
                locals(),
                file=pyfile,
            ))

    try:
        sig = inspect.signature(mod.migrate)
    except TypeError as e:
        raise TypeError("module %(addon)s: `migrate` needs to be a function, got %(migrate)r" % dict(locals(), migrate=mod.migrate)) from e

    if not (
            tuple(sig.parameters.keys()) in VALID_MIGRATE_PARAMS
        and all(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in sig.parameters.values())
    ):
        raise TypeError("module %(addon)s: `migrate`'s signature should be `(cr, version)`, %(func)s is %(sig)s" % dict(locals(), func=mod.migrate, sig=sig))

    _logger.info('module %(addon)s: Running migration %(version)s %(name)s' % dict(locals(), name=mod.__name__))  # noqa: G002
    mod.migrate(cr, installed_version)