def test_lambdas(self):
        # self.assertEqual(get_hash(lambda x: x.lower()), get_hash(lambda x: x.lower()))
        self.assertNotEqual(
            get_hash(lambda x: x.lower()), get_hash(lambda x: x.upper())
        )