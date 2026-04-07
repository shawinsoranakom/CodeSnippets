def test_delete_all_sites_clears_cache(self):
        # When all site objects are deleted the cache should also
        # be cleared and get_current() should raise a DoesNotExist.
        self.assertIsInstance(Site.objects.get_current(), Site)
        Site.objects.all().delete()
        with self.assertRaises(Site.DoesNotExist):
            Site.objects.get_current()