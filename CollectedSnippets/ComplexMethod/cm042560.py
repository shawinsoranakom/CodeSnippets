def test_normvalue(self):
        class MyDict(self.dict_class):
            def _normvalue(self, value):
                if value is not None:
                    return value + 1
                return None

            normvalue = _normvalue  # deprecated CaselessDict class

        d = MyDict({"key": 1})
        assert d["key"] == 2
        assert d.get("key") == 2

        d = MyDict()
        d["key"] = 1
        assert d["key"] == 2
        assert d.get("key") == 2

        d = MyDict()
        d.setdefault("key", 1)
        assert d["key"] == 2
        assert d.get("key") == 2

        d = MyDict()
        d.update({"key": 1})
        assert d["key"] == 2
        assert d.get("key") == 2

        d = MyDict.fromkeys(("key",), 1)
        assert d["key"] == 2
        assert d.get("key") == 2