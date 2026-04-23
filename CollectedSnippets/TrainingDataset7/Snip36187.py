def test_update_with_empty_iterable(self):
        for value in ["", b"", (), [], set(), {}]:
            d = MultiValueDict()
            d.update(value)
            self.assertEqual(d, MultiValueDict())