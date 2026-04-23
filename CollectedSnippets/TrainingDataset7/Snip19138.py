def test_set_fail_on_pickleerror(self):
        with self.assertRaises(pickle.PickleError):
            cache.set("unpicklable", Unpicklable())