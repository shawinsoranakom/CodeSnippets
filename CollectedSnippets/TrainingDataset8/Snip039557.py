def test_hash_funcs_acceptable_keys(self):
        class C(object):
            def __init__(self):
                self.x = (x for x in range(1))

        with self.assertRaises(UnhashableTypeError):
            get_hash(C())

        self.assertEqual(
            get_hash(C(), hash_funcs={types.GeneratorType: id}),
            get_hash(C(), hash_funcs={"builtins.generator": id}),
        )