def caches_setting_for_tests(base=None, exclude=None, **params):
    # `base` is used to pull in the memcached config from the original
    # settings, `exclude` is a set of cache names denoting which
    # `_caches_setting_base` keys should be omitted. `params` are test specific
    # overrides and `_caches_settings_base` is the base config for the tests.
    # This results in the following search order:
    # params -> _caches_setting_base -> base
    base = base or {}
    exclude = exclude or set()
    setting = {k: base.copy() for k in _caches_setting_base if k not in exclude}
    for key, cache_params in setting.items():
        cache_params.update(_caches_setting_base[key])
        cache_params.update(params)
    return setting