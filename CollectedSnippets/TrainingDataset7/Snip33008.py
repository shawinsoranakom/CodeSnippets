def test_linenumbers(self):
        self.assertEqual(linenumbers("line 1\nline 2"), "1. line 1\n2. line 2")