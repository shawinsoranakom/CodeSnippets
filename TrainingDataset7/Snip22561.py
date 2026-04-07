def test_file_picklable(self):
        self.assertIsInstance(pickle.loads(pickle.dumps(FileField())), FileField)