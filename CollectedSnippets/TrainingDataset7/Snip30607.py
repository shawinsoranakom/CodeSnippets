def test_deferred_load_qs_pickling(self):
        # Check pickling of deferred-loading querysets
        qs = Item.objects.defer("name", "creator")
        q2 = pickle.loads(pickle.dumps(qs))
        self.assertEqual(list(qs), list(q2))
        q3 = pickle.loads(pickle.dumps(qs, pickle.HIGHEST_PROTOCOL))
        self.assertEqual(list(qs), list(q3))