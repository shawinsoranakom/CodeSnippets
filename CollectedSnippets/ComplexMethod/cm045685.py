def import_object(path: str) -> object:
    if path.startswith("pw.") or path.startswith("pw:"):
        path = "pathway" + path.removeprefix("pw")

    module_path, colon, attribute_path = path.partition(":")

    attributes = attribute_path.split(".") if attribute_path else []

    module = builtins
    if not colon:
        names = module_path.split(".") if module_path else []
        for index, name in enumerate(names):
            prefix = ".".join(names[: index + 1])
            try:
                module = importlib.import_module(prefix)
            except ModuleNotFoundError:
                attributes = names[index:]
                break
    elif module_path:
        module = importlib.import_module(module_path)

    res = module
    for attribute in attributes:
        res = getattr(res, attribute)

    return res