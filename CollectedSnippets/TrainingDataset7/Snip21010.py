def test_defer_none_to_clear_deferred_set(self):
        qs = Primary.objects.all()
        self.assert_delayed(qs.defer("name", "value")[0], 2)
        self.assert_delayed(qs.defer(None)[0], 0)
        self.assert_delayed(qs.only("name").defer(None)[0], 0)