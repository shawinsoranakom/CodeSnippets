def _run_operation(obj, fun, *args):
    try:
        return fun(obj, *args), None
    except Exception as e:
        return None, e
