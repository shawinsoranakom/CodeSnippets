def block_algorithm(name, *, allow_openssl=False, allow_builtin=False):
    """Block a hash algorithm for both hashing and HMAC.

    Be careful with this helper as a function may be allowed, but can
    still raise a ValueError at runtime if the OpenSSL security policy
    disables it, e.g., if allow_openssl=True and FIPS mode is on.
    """
    with contextlib.ExitStack() as stack:
        if not (allow_openssl or allow_builtin):
            # Named constructors have a different behavior in the sense
            # that they are either built-ins or OpenSSL ones, but not
            # "agile" ones (namely once "hashlib" has been imported,
            # they are fixed).
            #
            # If OpenSSL is not available, hashes fall back to built-in ones,
            # in which case we don't need to block the explicit public hashes
            # as they will call a mocked one.
            #
            # If OpenSSL is available, hashes fall back to "openssl_*" ones,
            # except for BLAKE2b and BLAKE2s.
            stack.enter_context(_block_hashlib_hash_constructor(name))
        elif (
            # In FIPS mode, hashlib.<name>() functions may raise if they use
            # the OpenSSL implementation, except with usedforsecurity=False.
            # However, blocking such functions also means blocking them
            # so we again need to block them if we want to.
            (_hashlib := _import_module("_hashlib"))
            and _hashlib.get_fips_mode()
            and not allow_openssl
        ) or (
            # Without OpenSSL, hashlib.<name>() functions are aliases
            # to built-in functions, so both of them must be blocked
            # as the module may have been imported before the HACL ones.
            not (_hashlib := _import_module("_hashlib"))
            and not allow_builtin
        ):
            stack.enter_context(_block_hashlib_hash_constructor(name))

        if not allow_openssl:
            # _hashlib.new()
            stack.enter_context(_block_openssl_hash_new(name))
            # _hashlib.openssl_*()
            stack.enter_context(_block_openssl_hash_constructor(name))
            # _hashlib.hmac_new()
            stack.enter_context(_block_openssl_hmac_new(name))
            # _hashlib.hmac_digest()
            stack.enter_context(_block_openssl_hmac_digest(name))

        if not allow_builtin:
            # __get_builtin_constructor(name)
            stack.enter_context(_block_builtin_hash_new(name))
            # <built-in module>.<built-in name>()
            stack.enter_context(_block_builtin_hash_constructor(name))
            # _hmac.new(..., name)
            stack.enter_context(_block_builtin_hmac_new(name))
            # _hmac.compute_<name>()
            stack.enter_context(_block_builtin_hmac_constructor(name))
            # _hmac.compute_digest(..., name)
            stack.enter_context(_block_builtin_hmac_digest(name))
        yield