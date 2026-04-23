def compare_dicts(old, new):
    """Compare the old and new dicts and print the differences."""
    added = new.keys() - old.keys()
    if added:
        print(f'{len(added)} entitie(s) have been added:')
        for name in sorted(added):
            print(f'  {name!r}: {new[name]!r}')
    removed = old.keys() - new.keys()
    if removed:
        print(f'{len(removed)} entitie(s) have been removed:')
        for name in sorted(removed):
            print(f'  {name!r}: {old[name]!r}')
    changed = set()
    for name in (old.keys() & new.keys()):
        if old[name] != new[name]:
            changed.add((name, old[name], new[name]))
    if changed:
        print(f'{len(changed)} entitie(s) have been modified:')
        for item in sorted(changed):
            print('  {!r}: {!r} -> {!r}'.format(*item))