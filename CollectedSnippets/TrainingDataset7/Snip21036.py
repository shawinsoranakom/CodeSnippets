def test_defer_subclass_both(self):
        # Deferring fields from both superclass and subclass works.
        obj = BigChild.objects.defer("other", "value").get(name="b1")
        self.assert_delayed(obj, 2)