def test_copy(self):
        h1 = self.dict_class({"header1": "value"})
        h2 = copy.copy(h1)
        assert isinstance(h2, self.dict_class)
        assert h1 == h2
        assert h1.get("header1") == h2.get("header1")
        assert h1.get("header1") == h2.get("HEADER1")
        h3 = h1.copy()
        assert isinstance(h3, self.dict_class)
        assert h1 == h3
        assert h1.get("header1") == h3.get("header1")
        assert h1.get("header1") == h3.get("HEADER1")