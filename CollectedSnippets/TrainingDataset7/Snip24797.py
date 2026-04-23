def test_fromkeys_noniterable(self):
        with self.assertRaises(TypeError):
            QueryDict.fromkeys(0)