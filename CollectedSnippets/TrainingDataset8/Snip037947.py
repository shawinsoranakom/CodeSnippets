def __init__(self, hash_funcs: Optional[HashFuncsDict] = None):
        # Can't use types as the keys in the internal _hash_funcs because
        # we always remove user-written modules from memory when rerunning a
        # script in order to reload it and grab the latest code changes.
        # (See LocalSourcesWatcher.py:on_file_changed) This causes
        # the type object to refer to different underlying class instances each run,
        # so type-based comparisons fail. To solve this, we use the types converted
        # to fully-qualified strings as keys in our internal dict.
        self._hash_funcs: HashFuncsDict
        if hash_funcs:
            self._hash_funcs = {
                k if isinstance(k, str) else type_util.get_fqn(k): v
                for k, v in hash_funcs.items()
            }
        else:
            self._hash_funcs = {}

        self._hashes: Dict[Any, bytes] = {}

        # The number of the bytes in the hash.
        self.size = 0