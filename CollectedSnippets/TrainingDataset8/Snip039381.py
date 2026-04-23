def test_dataclass(self):
        @dataclass(frozen=True, eq=True)
        class Data:
            foo: str

        bar = Data("bar")

        assert get_hash(bar)