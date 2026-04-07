def test_defer_extra(self):
        qs = Primary.objects.all()
        self.assert_delayed(qs.defer("name").extra(select={"a": 1})[0], 1)
        self.assert_delayed(qs.extra(select={"a": 1}).defer("name")[0], 1)