def get_hash(f, context=None, hash_funcs=None):
    hasher = hashlib.new("md5")
    ch = _CodeHasher(hash_funcs=hash_funcs)
    ch._get_main_script_directory = MagicMock()
    ch._get_main_script_directory.return_value = os.getcwd()
    ch.update(hasher, f, context)
    return hasher.digest()