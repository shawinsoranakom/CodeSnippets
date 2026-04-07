def test_boolean_picklable(self):
        self.assertIsInstance(pickle.loads(pickle.dumps(BooleanField())), BooleanField)