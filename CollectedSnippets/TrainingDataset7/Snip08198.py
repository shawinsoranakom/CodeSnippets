def default_key_func(key, key_prefix, version):
    """
    Default function to generate keys.

    Construct the key used by all other methods. By default, prepend
    the `key_prefix`. KEY_FUNCTION can be used to specify an alternate
    function with custom key making behavior.
    """
    return "%s:%s:%s" % (key_prefix, version, key)