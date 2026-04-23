def _add_security_filters(base, bugfix, security):
    """Add security and bugfix filters for package upgrades."""
    add_security_filters_method = getattr(base, 'add_security_filters', None)
    if callable(add_security_filters_method):
        filters = {}
        if bugfix:
            filters.setdefault('types', []).append('bugfix')
        if security:
            filters.setdefault('types', []).append('security')
        if filters:
            add_security_filters_method('eq', **filters)
    else:
        # Fallback for older dnf versions
        filters = []
        if bugfix:
            key = {'advisory_type__eq': 'bugfix'}
            filters.append(base.sack.query().upgrades().filter(**key))
        if security:
            key = {'advisory_type__eq': 'security'}
            filters.append(base.sack.query().upgrades().filter(**key))
        if filters:
            base._update_security_filters = filters

    return True