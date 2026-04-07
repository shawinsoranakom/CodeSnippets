def test_defer_only_chaining(self):
        qs = Primary.objects.all()
        self.assert_delayed(qs.only("name", "value").defer("name")[0], 2)
        self.assert_delayed(qs.defer("name").only("value", "name")[0], 2)
        self.assert_delayed(qs.defer("name").only("name").only("value")[0], 2)
        self.assert_delayed(qs.defer("name").only("value")[0], 2)
        self.assert_delayed(qs.only("name").defer("value")[0], 2)
        self.assert_delayed(qs.only("name").defer("name").defer("value")[0], 1)
        self.assert_delayed(qs.only("name").defer("name", "value")[0], 1)