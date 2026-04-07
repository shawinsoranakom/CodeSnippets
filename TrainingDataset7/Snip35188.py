def test_binaryfield_data_type(self):
        self.assertEqual(bytes(self.person_binary.data), b"binary data")
        self.assertEqual(bytes(self.person_binary_get.data), b"binary data")
        self.assertEqual(
            type(self.person_binary_get.data),
            type(self.__class__.person_binary_get.data),
        )
        self.assertEqual(
            type(self.person_binary.data),
            type(self.__class__.person_binary.data),
        )