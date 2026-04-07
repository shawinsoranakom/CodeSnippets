def test_inherited_overriden_property_no_clash(self):
        class Cheese:
            @property
            def filling_id(self):
                pass

        class Sandwich(Cheese, models.Model):
            filling = models.ForeignKey("self", models.CASCADE)

        self.assertEqual(Sandwich.check(), [])