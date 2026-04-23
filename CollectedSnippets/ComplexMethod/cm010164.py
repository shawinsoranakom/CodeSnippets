def _collect_examples():
    case_names = glob.glob(join(dirname(__file__), "*.py"))
    case_names = [
        basename(f)[:-3] for f in case_names if isfile(f) and not f.endswith("__init__.py")
    ]

    case_fields = {f.name for f in dataclasses.fields(ExportCase)}
    for case_name in case_names:
        case = __import__(case_name, globals(), locals(), [], 1)
        variables = [name for name in dir(case) if name in case_fields]
        export_case(**{v: getattr(case, v) for v in variables})(case.model)