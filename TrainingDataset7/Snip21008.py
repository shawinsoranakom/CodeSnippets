def test_defer_only_clear(self):
        qs = Primary.objects.all()
        self.assert_delayed(qs.only("name").defer("name")[0], 0)
        self.assert_delayed(qs.defer("name").only("name")[0], 0)