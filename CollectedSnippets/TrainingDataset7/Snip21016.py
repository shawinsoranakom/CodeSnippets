def test_get(self):
        # Using defer() and only() with get() is also valid.
        qs = Primary.objects.all()
        self.assert_delayed(qs.defer("name").get(pk=self.p1.pk), 1)
        self.assert_delayed(qs.only("name").get(pk=self.p1.pk), 2)