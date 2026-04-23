def test_fromkeys(self):
        keys = ("a", "b")

        d = self.dict_class.fromkeys(keys)
        assert d["A"] is None
        assert d["B"] is None

        d = self.dict_class.fromkeys(keys, 1)
        assert d["A"] == 1
        assert d["B"] == 1

        instance = self.dict_class()
        d = instance.fromkeys(keys)
        assert d["A"] is None
        assert d["B"] is None

        d = instance.fromkeys(keys, 1)
        assert d["A"] == 1
        assert d["B"] == 1