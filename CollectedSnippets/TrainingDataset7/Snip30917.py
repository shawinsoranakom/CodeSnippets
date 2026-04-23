def test_string_as_default(self):
        self.assert_pickles(Happening.objects.filter(name="test"))