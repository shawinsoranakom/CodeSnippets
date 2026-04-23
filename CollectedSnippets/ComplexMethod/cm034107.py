def list_items(config, command):
    """List packages based on command."""
    base = None
    try:
        base, module_base, warnings = _setup_base(config)

        if command == 'updates':
            command = 'upgrades'

        if command == 'installed':
            results = list(base.sack.query().installed())
        elif command == 'upgrades':
            results = list(base.sack.query().upgrades())
        elif command == 'available':
            results = list(base.sack.query().available())
        elif command in ['repos', 'repositories']:
            results = [{'repoid': repo.id, 'state': 'enabled'} for repo in base.repos.iter_enabled()]
        else:
            results = list(dnf.subject.Subject(command).get_best_query(base.sack))

        return {'results': results, 'warnings': warnings}
    except Exception as e:
        return {'results': [], 'warnings': [], 'failed': True, 'msg': f'{e}'}
    finally:
        if base:
            base.close()