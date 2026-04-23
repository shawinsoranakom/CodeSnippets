def build_excinfo(exctype, msg=None, formatted=None, errdisplay=None):
    if isinstance(exctype, type):
        assert issubclass(exctype, BaseException), exctype
        exctype = types.SimpleNamespace(
            __name__=exctype.__name__,
            __qualname__=exctype.__qualname__,
            __module__=exctype.__module__,
        )
    elif isinstance(exctype, str):
        module, _, name = exctype.rpartition(exctype)
        if not module and name in __builtins__:
            module = 'builtins'
        exctype = types.SimpleNamespace(
            __name__=name,
            __qualname__=exctype,
            __module__=module or None,
        )
    else:
        assert isinstance(exctype, types.SimpleNamespace)
    assert msg is None or isinstance(msg, str), msg
    assert formatted  is None or isinstance(formatted, str), formatted
    assert errdisplay is None or isinstance(errdisplay, str), errdisplay
    return types.SimpleNamespace(
        type=exctype,
        msg=msg,
        formatted=formatted,
        errdisplay=errdisplay,
    )