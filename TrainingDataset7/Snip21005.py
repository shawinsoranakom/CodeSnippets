def test_defer(self):
        qs = Primary.objects.all()
        self.assert_delayed(qs.defer("name")[0], 1)
        self.assert_delayed(qs.defer("name").get(pk=self.p1.pk), 1)
        self.assert_delayed(qs.defer("related__first")[0], 0)
        self.assert_delayed(qs.defer("name").defer("value")[0], 2)