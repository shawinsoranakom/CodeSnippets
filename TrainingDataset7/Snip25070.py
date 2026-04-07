def test_ngettext_lazy_pickle(self):
        s1 = ngettext_lazy("%d good result", "%d good results")
        self.assertEqual(s1 % 1, "1 good result")
        self.assertEqual(s1 % 8, "8 good results")
        s2 = pickle.loads(pickle.dumps(s1))
        self.assertEqual(s2 % 1, "1 good result")
        self.assertEqual(s2 % 8, "8 good results")