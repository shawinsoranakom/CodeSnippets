def test_infinite_loop(self):
        # If you're not careful, it's possible to introduce infinite loops via
        # default ordering on foreign keys in a cycle. We detect that.
        with self.assertRaisesMessage(FieldError, "Infinite loop caused by ordering."):
            list(LoopX.objects.all())  # Force queryset evaluation with list()
        with self.assertRaisesMessage(FieldError, "Infinite loop caused by ordering."):
            list(LoopZ.objects.all())  # Force queryset evaluation with list()

        # Note that this doesn't cause an infinite loop, since the default
        # ordering on the Tag model is empty (and thus defaults to using "id"
        # for the related field).
        self.assertEqual(len(Tag.objects.order_by("parent")), 5)

        # ... but you can still order in a non-recursive fashion among linked
        # fields (the previous test failed because the default ordering was
        # recursive).
        self.assertSequenceEqual(LoopX.objects.order_by("y__x__y__x__id"), [])