def collect_names(structure):
    if isinstance(structure, dict):
        for k, v in structure.items():
            if isinstance(v, (dict, list, tuple)):
                yield from collect_names(v)
            else:
                yield k
    elif isinstance(structure, (list, tuple)):
        for v in structure:
            yield from collect_names(v)
    else:
        if hasattr(structure, "name") and structure.name:
            yield structure.name
        else:
            yield "input"