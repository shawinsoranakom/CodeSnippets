def reset_hashers(*, setting, **kwargs):
    if setting == "PASSWORD_HASHERS":
        get_hashers.cache_clear()
        get_hashers_by_algorithm.cache_clear()