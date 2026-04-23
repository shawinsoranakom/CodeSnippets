def __init__(self, *args, **kwargs):
        algorithms = set()
        for algorithm in self.supported_hash_names:
            algorithms.add(algorithm.lower())

        _blake2 = self._conditional_import_module('_blake2')
        blake2_hashes = {'blake2b', 'blake2s'}
        if _blake2:
            algorithms.update(blake2_hashes)
        else:
            algorithms.difference_update(blake2_hashes)

        self.constructors_to_test = {}
        for algorithm in algorithms:
            self.constructors_to_test[algorithm] = set()

        # For each algorithm, test the direct constructor and the use
        # of hashlib.new given the algorithm name.
        for algorithm, constructors in self.constructors_to_test.items():
            constructors.add(getattr(hashlib, algorithm))
            def c(*args, __algorithm_name=algorithm, **kwargs):
                return hashlib.new(__algorithm_name, *args, **kwargs)
            c.__name__ = f'do_test_algorithm_via_hashlib_new_{algorithm}'
            constructors.add(c)

        _hashlib = self._conditional_import_module('_hashlib')
        self._hashlib = _hashlib
        if _hashlib:
            # These algorithms should always be present when this module
            # is compiled.  If not, something was compiled wrong.
            self.assertHasAttr(_hashlib, 'openssl_md5')
            self.assertHasAttr(_hashlib, 'openssl_sha1')
            for algorithm, constructors in self.constructors_to_test.items():
                constructor = getattr(_hashlib, 'openssl_'+algorithm, None)
                if constructor:
                    try:
                        constructor()
                    except ValueError:
                        # default constructor blocked by crypto policy
                        pass
                    else:
                        constructors.add(constructor)

        def add_builtin_constructor(name):
            constructor = getattr(hashlib, "__get_builtin_constructor")(name)
            self.constructors_to_test[name].add(constructor)

        _md5 = self._conditional_import_module('_md5')
        if _md5:
            add_builtin_constructor('md5')
        _sha1 = self._conditional_import_module('_sha1')
        if _sha1:
            add_builtin_constructor('sha1')
        _sha2 = self._conditional_import_module('_sha2')
        if _sha2:
            add_builtin_constructor('sha224')
            add_builtin_constructor('sha256')
            add_builtin_constructor('sha384')
            add_builtin_constructor('sha512')
        _sha3 = self._conditional_import_module('_sha3')
        if _sha3:
            add_builtin_constructor('sha3_224')
            add_builtin_constructor('sha3_256')
            add_builtin_constructor('sha3_384')
            add_builtin_constructor('sha3_512')
            add_builtin_constructor('shake_128')
            add_builtin_constructor('shake_256')
        if _blake2:
            add_builtin_constructor('blake2s')
            add_builtin_constructor('blake2b')

        super(HashLibTestCase, self).__init__(*args, **kwargs)