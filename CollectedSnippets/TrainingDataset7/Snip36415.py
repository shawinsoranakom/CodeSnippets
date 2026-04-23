def test_custom_iterable_not_doseq(self):
        class IterableWithStr:
            def __str__(self):
                return "custom"

            def __iter__(self):
                yield from range(0, 3)

        self.assertEqual(urlencode({"a": IterableWithStr()}, doseq=False), "a=custom")