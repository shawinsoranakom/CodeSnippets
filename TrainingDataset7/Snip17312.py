def test_repr(self):
        ac = AppConfig("label", Stub(__path__=["a"]))
        self.assertEqual(repr(ac), "<AppConfig: label>")