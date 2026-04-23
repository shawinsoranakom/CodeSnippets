def _mro_matches(
    dataset, class_names, module_prefixes=(), module_substrings=()
):
    if not hasattr(dataset, "__class__"):
        return False
    for parent in dataset.__class__.__mro__:
        if parent.__name__ in class_names:
            mod = str(parent.__module__)
            if any(mod.startswith(pref) for pref in module_prefixes):
                return True
            if any(subs in mod for subs in module_substrings):
                return True
    return False