def test_filter_by_pk_in_none(self):
        with self.assertNumQueries(0):
            self.assertSequenceEqual(
                Comment.objects.filter(pk__in=[(None, 1), (1, None)]),
                [],
            )