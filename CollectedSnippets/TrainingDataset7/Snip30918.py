def test_standalone_method_as_default(self):
        self.assert_pickles(Happening.objects.filter(number1=1))