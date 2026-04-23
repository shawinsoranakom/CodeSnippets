def _get_random_filename(max_random_bytes):
    return b"a" * secrets.randbelow(max_random_bytes)