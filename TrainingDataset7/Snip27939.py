def test_pickle(self):
        """
        ImageField can be pickled, unpickled, and that the image of
        the unpickled version is the same as the original.
        """
        import pickle

        p = Person(name="Joe")
        p.mugshot.save("mug", self.file1)
        dump = pickle.dumps(p)

        loaded_p = pickle.loads(dump)
        self.assertEqual(p.mugshot, loaded_p.mugshot)
        self.assertEqual(p.mugshot.url, loaded_p.mugshot.url)
        self.assertEqual(p.mugshot.storage, loaded_p.mugshot.storage)
        self.assertEqual(p.mugshot.instance, loaded_p.mugshot.instance)
        self.assertEqual(p.mugshot.field, loaded_p.mugshot.field)

        mugshot_dump = pickle.dumps(p.mugshot)
        loaded_mugshot = pickle.loads(mugshot_dump)
        self.assertEqual(p.mugshot, loaded_mugshot)
        self.assertEqual(p.mugshot.url, loaded_mugshot.url)
        self.assertEqual(p.mugshot.storage, loaded_mugshot.storage)
        self.assertEqual(p.mugshot.instance, loaded_mugshot.instance)
        self.assertEqual(p.mugshot.field, loaded_mugshot.field)