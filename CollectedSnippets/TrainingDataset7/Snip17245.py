def test_order_by_alias(self):
        qs = Author.objects.alias(other_age=F("age")).order_by("other_age")
        self.assertIs(hasattr(qs.first(), "other_age"), False)
        self.assertQuerySetEqual(qs, [34, 34, 35, 46, 57], lambda a: a.age)