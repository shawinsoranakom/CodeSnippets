def test_fast_delete_combined_relationships(self):
        # The cascading fast-delete of SecondReferrer should be combined
        # in a single DELETE WHERE referrer_id OR unique_field.
        origin = Origin.objects.create()
        referer = Referrer.objects.create(origin=origin, unique_field=42)
        with self.assertNumQueries(2):
            referer.delete()