def test_arg_to_iter(self):
        class TestItem(Item):
            name = Field()

        assert hasattr(arg_to_iter(None), "__iter__")
        assert hasattr(arg_to_iter(100), "__iter__")
        assert hasattr(arg_to_iter("lala"), "__iter__")
        assert hasattr(arg_to_iter([1, 2, 3]), "__iter__")
        assert hasattr(arg_to_iter(c for c in "abcd"), "__iter__")

        assert not list(arg_to_iter(None))
        assert list(arg_to_iter("lala")) == ["lala"]
        assert list(arg_to_iter(100)) == [100]
        assert list(arg_to_iter(c for c in "abc")) == ["a", "b", "c"]
        assert list(arg_to_iter([1, 2, 3])) == [1, 2, 3]
        assert list(arg_to_iter({"a": 1})) == [{"a": 1}]
        assert list(arg_to_iter(TestItem(name="john"))) == [TestItem(name="john")]