def test_getset_descriptor(self):
        class A:
            x = 1

        class B:
            x = 1

        a = A.__dict__["__dict__"]
        b = B.__dict__["__dict__"]
        assert is_type(a, "builtins.getset_descriptor")

        self.assertEqual(get_hash(a), get_hash(a))
        self.assertNotEqual(get_hash(a), get_hash(b))