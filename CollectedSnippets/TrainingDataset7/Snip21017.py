def test_defer_with_select_related(self):
        obj = Primary.objects.select_related().defer(
            "related__first", "related__second"
        )[0]
        self.assert_delayed(obj.related, 2)
        self.assert_delayed(obj, 0)