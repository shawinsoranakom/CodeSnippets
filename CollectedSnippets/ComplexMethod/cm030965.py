def run_in_subinterp_with_config(code, *, own_gil=None, **config):
    """
    Run code in a subinterpreter. Raise unittest.SkipTest if the tracemalloc
    module is enabled.
    """
    _check_tracemalloc()
    try:
        import _testinternalcapi
    except ImportError:
        raise unittest.SkipTest("requires _testinternalcapi")
    if own_gil is not None:
        assert 'gil' not in config, (own_gil, config)
        config['gil'] = 'own' if own_gil else 'shared'
    else:
        gil = config['gil']
        if gil == 0:
            config['gil'] = 'default'
        elif gil == 1:
            config['gil'] = 'shared'
        elif gil == 2:
            config['gil'] = 'own'
        elif not isinstance(gil, str):
            raise NotImplementedError(gil)
    config = types.SimpleNamespace(**config)
    return _testinternalcapi.run_in_subinterp_with_config(code, config)