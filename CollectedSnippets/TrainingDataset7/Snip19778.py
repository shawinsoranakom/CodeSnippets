def test_deconstruction(self):
        check = models.Q(price__gt=models.F("discounted_price"))
        name = "price_gt_discounted_price"
        constraint = models.CheckConstraint(condition=check, name=name)
        path, args, kwargs = constraint.deconstruct()
        self.assertEqual(path, "django.db.models.CheckConstraint")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"condition": check, "name": name})