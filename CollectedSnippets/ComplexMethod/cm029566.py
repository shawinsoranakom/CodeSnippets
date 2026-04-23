def _get_registry_entries(ns, root="", d=None):
    r = root if root else PureWindowsPath("")
    if d is None:
        d = REGISTRY
    for key, value in d.items():
        if key == "_condition":
            continue
        if value is SPECIAL_LOOKUP:
            if key == "SysArchitecture":
                value = {
                    "win32": "32bit",
                    "amd64": "64bit",
                    "arm32": "32bit",
                    "arm64": "64bit",
                }[ns.arch]
            else:
                raise ValueError(f"Key '{key}' unhandled for special lookup")
        if isinstance(value, dict):
            cond = value.get("_condition")
            if cond and not cond(ns):
                continue
            fullkey = r
            for part in PureWindowsPath(key).parts:
                fullkey /= part
                if len(fullkey.parts) > 1:
                    yield str(fullkey), None, None
            yield from _get_registry_entries(ns, fullkey, value)
        elif len(r.parts) > 1:
            yield str(r), key, value