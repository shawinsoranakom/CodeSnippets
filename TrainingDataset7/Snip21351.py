def test_update_with_fk(self):
        # ForeignKey can become updated with the value of another ForeignKey.
        self.assertEqual(Company.objects.update(point_of_contact=F("ceo")), 3)
        self.assertQuerySetEqual(
            Company.objects.all(),
            ["Joe Smith", "Frank Meyer", "Max Mustermann"],
            lambda c: str(c.point_of_contact),
            ordered=False,
        )