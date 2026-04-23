def test_defer_on_an_already_deferred_field(self):
        qs = Primary.objects.all()
        self.assert_delayed(qs.defer("name")[0], 1)
        self.assert_delayed(qs.defer("name").defer("name")[0], 1)