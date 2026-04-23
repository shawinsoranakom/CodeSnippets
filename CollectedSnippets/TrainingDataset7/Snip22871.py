def test_empty_data_files_multi_value_dict(self):
        p = Person()
        self.assertIsInstance(p.data, MultiValueDict)
        self.assertIsInstance(p.files, MultiValueDict)