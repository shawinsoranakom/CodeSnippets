def test_staticmethod_as_default(self):
        self.assert_pickles(Happening.objects.filter(number2=1))