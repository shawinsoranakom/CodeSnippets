def test_pickle(self):
        x = MultiValueDict({"a": ["1", "2"], "b": ["3"]})
        self.assertEqual(x, pickle.loads(pickle.dumps(x)))