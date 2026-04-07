def test_get_prefetch_querysets_invalid_querysets_length(self):
        places = Place.objects.all()
        msg = (
            "querysets argument of get_prefetch_querysets() should have a length of 1."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Place.bar.get_prefetch_querysets(
                instances=places,
                querysets=[Bar.objects.all(), Bar.objects.all()],
            )