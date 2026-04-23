def test_values_with_percent(self):
        searched = Line.objects.annotate(
            search=SearchVector(Value("This week everything is 10% off"))
        ).filter(search="10 % off")
        self.assertEqual(len(searched), 9)