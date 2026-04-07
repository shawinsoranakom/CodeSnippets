def test_regression_19870(self):
        hen = Hen.objects.create(name="Hen")
        Chick.objects.create(name="Chick", mother=hen)

        self.assertEqual(Chick.objects.all()[0].mother.name, "Hen")
        self.assertEqual(Chick.objects.select_related()[0].mother.name, "Hen")