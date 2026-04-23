def test_load_library_no_algorithm(self):
        msg = "Hasher 'BasePasswordHasher' doesn't specify a library attribute"
        with self.assertRaisesMessage(ValueError, msg):
            self.hasher._load_library()