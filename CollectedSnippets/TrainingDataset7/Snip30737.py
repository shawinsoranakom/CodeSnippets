def test_emptyqueryset_values(self):
        # #14366 -- Calling .values() on an empty QuerySet and then cloning
        # that should not cause an error
        self.assertCountEqual(Number.objects.none().values("num").order_by("num"), [])