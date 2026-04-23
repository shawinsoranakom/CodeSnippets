def test_truncate_something(self):
        self.assertEqual(truncatechars_html("a<b>b</b>c", 3), "a<b>b</b>c")