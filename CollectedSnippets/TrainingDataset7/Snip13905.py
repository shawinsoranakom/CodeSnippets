def assertQuerySetEqual(self, qs, values, transform=None, ordered=True, msg=None):
        values = list(values)
        items = qs
        if transform is not None:
            items = map(transform, items)
        if not ordered:
            return self.assertDictEqual(Counter(items), Counter(values), msg=msg)
        # For example qs.iterator() could be passed as qs, but it does not
        # have 'ordered' attribute.
        if len(values) > 1 and hasattr(qs, "ordered") and not qs.ordered:
            raise ValueError(
                "Trying to compare non-ordered queryset against more than one "
                "ordered value."
            )
        return self.assertEqual(list(items), values, msg=msg)