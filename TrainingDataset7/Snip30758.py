def test_named_values_pickle(self):
        value = Number.objects.values_list("num", "other_num", named=True).get()
        self.assertEqual(value, (72, None))
        self.assertEqual(pickle.loads(pickle.dumps(value)), value)