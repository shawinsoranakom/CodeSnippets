def test_update_no_args(self):
        x = MultiValueDict({"a": []})
        x.update()
        self.assertEqual(list(x.lists()), [("a", [])])