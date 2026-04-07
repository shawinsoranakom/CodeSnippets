def test_find_all(self):
        src, dst = self.find_all
        found = self.finder.find(src, find_all=True)
        found = [os.path.normcase(f) for f in found]
        dst = [os.path.normcase(d) for d in dst]
        self.assertEqual(found, dst)