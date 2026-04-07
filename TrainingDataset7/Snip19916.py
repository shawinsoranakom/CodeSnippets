def test_lookup_cache(self):
        """
        The content type cache (see ContentTypeManager) works correctly.
        Lookups for a particular content type -- by model, ID, or natural key
        -- should hit the database only on the first lookup.
        """
        # At this point, a lookup for a ContentType should hit the DB
        with self.assertNumQueries(1):
            ContentType.objects.get_for_model(ContentType)

        # A second hit, though, won't hit the DB, nor will a lookup by ID
        # or natural key
        with self.assertNumQueries(0):
            ct = ContentType.objects.get_for_model(ContentType)
        with self.assertNumQueries(0):
            ContentType.objects.get_for_id(ct.id)
        with self.assertNumQueries(0):
            ContentType.objects.get_by_natural_key("contenttypes", "contenttype")

        # Once we clear the cache, another lookup will again hit the DB
        ContentType.objects.clear_cache()
        with self.assertNumQueries(1):
            ContentType.objects.get_for_model(ContentType)

        # The same should happen with a lookup by natural key
        ContentType.objects.clear_cache()
        with self.assertNumQueries(1):
            ContentType.objects.get_by_natural_key("contenttypes", "contenttype")
        # And a second hit shouldn't hit the DB
        with self.assertNumQueries(0):
            ContentType.objects.get_by_natural_key("contenttypes", "contenttype")