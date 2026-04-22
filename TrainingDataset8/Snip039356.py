def get_hash(f):
    hasher = hashlib.new("md5")
    ch = _CacheFuncHasher(MagicMock())
    ch.update(hasher, f)
    return hasher.digest()