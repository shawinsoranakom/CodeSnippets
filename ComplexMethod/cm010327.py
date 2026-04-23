def find_legit_leaks_from_referrers(active_fakes: weakref.WeakSet) -> weakref.WeakSet:
    legit_leak: weakref.WeakSet = weakref.WeakSet()

    # This is so that we don't falsely flag generator to be holding fake tensor
    fake_list = list(active_fakes)
    fake_list_id = id(fake_list)

    for act in fake_list:
        # Track by id to avoid processing duplicate referrers
        seen = set()
        # Assume it's a leak unless we find only ignorable referrers
        flagged = False

        for r in gc.get_referrers(act):
            rid = id(r)
            if rid in seen:
                continue
            seen.add(rid)

            # Skip our own fake_list
            if rid == fake_list_id:
                continue

            # Fast-path: skip obvious non-owners
            if _is_globals_or_locals(r):
                continue
            if isinstance(r, _SKIP_TYPES):
                continue
            if _is_tracked_fake(r):
                # TrackedFake should be ignored
                continue

            # Handle dicts carefully (Python 3.10 sometimes shows __dict__)
            if isinstance(r, dict):
                if _is_gm_meta_like_dict(r, act):
                    continue
                if _dict_is_attr_of_tracked_fake(r):
                    continue
                flagged = True
                break

            # Any other referrer we don't explicitly whitelist counts as a leak
            flagged = True
            break

        if flagged:
            legit_leak.add(act)

    return legit_leak