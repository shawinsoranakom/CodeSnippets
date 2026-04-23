def dependency_ordered(test_databases, dependencies):
    """
    Reorder test_databases into an order that honors the dependencies
    described in TEST[DEPENDENCIES].
    """
    ordered_test_databases = []
    resolved_databases = set()

    # Maps db signature to dependencies of all its aliases
    dependencies_map = {}

    # Check that no database depends on its own alias
    for sig, (_, aliases) in test_databases:
        all_deps = set()
        for alias in aliases:
            all_deps.update(dependencies.get(alias, []))
        if not all_deps.isdisjoint(aliases):
            raise ImproperlyConfigured(
                "Circular dependency: databases %r depend on each other, "
                "but are aliases." % aliases
            )
        dependencies_map[sig] = all_deps

    while test_databases:
        changed = False
        deferred = []

        # Try to find a DB that has all its dependencies met
        for signature, (db_name, aliases) in test_databases:
            if dependencies_map[signature].issubset(resolved_databases):
                resolved_databases.update(aliases)
                ordered_test_databases.append((signature, (db_name, aliases)))
                changed = True
            else:
                deferred.append((signature, (db_name, aliases)))

        if not changed:
            raise ImproperlyConfigured("Circular dependency in TEST[DEPENDENCIES]")
        test_databases = deferred
    return ordered_test_databases