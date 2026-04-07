def test_ticket10205(self):
        # When bailing out early because of an empty "__in" filter, we need
        # to set things up correctly internally so that subqueries can continue
        # properly.
        self.assertEqual(Tag.objects.filter(name__in=()).update(name="foo"), 0)