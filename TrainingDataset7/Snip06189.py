def verify_password(password, encoded, preferred="default"):
    """
    Return two booleans. The first is whether the raw password matches the
    three part encoded digest, and the second whether to regenerate the
    password.
    """
    fake_runtime = password is None or not is_password_usable(encoded)

    preferred = get_hasher(preferred)
    try:
        hasher = identify_hasher(encoded)
    except ValueError:
        # encoded is gibberish or uses a hasher that's no longer installed.
        fake_runtime = True

    if fake_runtime:
        # Run the default password hasher once to reduce the timing difference
        # between an existing user with an unusable password and a nonexistent
        # user or missing hasher (similar to #20760).
        make_password(get_random_string(UNUSABLE_PASSWORD_SUFFIX_LENGTH))
        return False, False

    hasher_changed = hasher.algorithm != preferred.algorithm
    must_update = hasher_changed or preferred.must_update(encoded)
    is_correct = hasher.verify(password, encoded)

    # If the hasher didn't change (we don't protect against enumeration if it
    # does) and the password should get updated, try to close the timing gap
    # between the work factor of the current encoded password and the default
    # work factor.
    if not is_correct and not hasher_changed and must_update:
        hasher.harden_runtime(password, encoded)

    return is_correct, must_update