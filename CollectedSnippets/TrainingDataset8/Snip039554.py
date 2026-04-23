def test_reduce_(self):
        class A(object):
            def __init__(self):
                self.x = [1, 2, 3]

        class B(object):
            def __init__(self):
                self.x = [1, 2, 3]

        class C(object):
            def __init__(self):
                self.x = (x for x in range(1))

        self.assertEqual(get_hash(A()), get_hash(A()))
        self.assertNotEqual(get_hash(A()), get_hash(B()))
        self.assertNotEqual(get_hash(A()), get_hash(A().__reduce__()))

        with self.assertRaises(UnhashableTypeError):
            get_hash(C())
        get_hash(C(), hash_funcs={types.GeneratorType: id})