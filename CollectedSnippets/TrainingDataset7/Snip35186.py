def test_class_attribute_equality(self):
        """Class level test data is equal to instance level test data."""
        self.assertEqual(self.jim_douglas, self.__class__.jim_douglas)
        self.assertEqual(self.person_binary, self.__class__.person_binary)
        self.assertEqual(self.person_binary_get, self.__class__.person_binary_get)