def filter_fuzzy_matches(missing: set[str], extra: set[str]) -> None:
    """
    Removes entries from `missing` and `extra` that share a common basename that also appears in `fuzzy_match_basenames`.
    Accounts for variable placement of non-runtime files by different versions of setuptools.
    """
    if not (missing or extra):
        return

    # calculate a set of basenames that appear in both missing and extra that are also marked as possibly needing fuzzy matching
    corresponding_fuzzy_basenames = {os.path.basename(p) for p in missing}.intersection(os.path.basename(p) for p in extra).intersection(fuzzy_match_basenames)

    # filter successfully fuzzy-matched entries from missing and extra
    missing.difference_update({p for p in missing if os.path.basename(p) in corresponding_fuzzy_basenames})
    extra.difference_update({p for p in extra if os.path.basename(p) in corresponding_fuzzy_basenames})