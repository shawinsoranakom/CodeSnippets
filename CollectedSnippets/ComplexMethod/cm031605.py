def do_check(baseline, checked, excluded, *, verbose_print):
    successful = True
    for name, baseline_ids in sorted(baseline.items()):
        try:
            checked_ids = checked[name]
        except KeyError:
            successful = False
            print(f'{name}: (page missing)')
            print()
        else:
            missing_ids = set(baseline_ids) - set(checked_ids)
            if missing_ids:
                missing_ids = {
                    a
                    for a in missing_ids
                    if not IGNORED_ID_RE.fullmatch(a)
                    and (name, a) not in excluded
                }
            if missing_ids:
                successful = False
                for missing_id in sorted(missing_ids):
                    print(f'{name}: {missing_id}')
                print()
    return successful