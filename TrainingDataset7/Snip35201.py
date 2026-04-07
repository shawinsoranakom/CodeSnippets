def test_fixture_loaded_during_class_setup(self):
        self.assertIsInstance(self.elvis, Person)