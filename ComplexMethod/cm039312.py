def get_all_methods():
    estimators = all_estimators()
    displays = all_displays()
    for name, Klass in estimators + displays:
        if name.startswith("_"):
            # skip private classes
            continue
        methods = []
        for name in dir(Klass):
            if name.startswith("_"):
                continue
            method_obj = getattr(Klass, name)
            if hasattr(method_obj, "__call__") or isinstance(method_obj, property):
                methods.append(name)
        methods.append(None)

        for method in sorted(methods, key=str):
            yield Klass, method