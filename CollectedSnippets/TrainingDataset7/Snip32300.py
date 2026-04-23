def test_site_manager(self):
        # Make sure that get_current() does not return a deleted Site object.
        s = Site.objects.get_current()
        self.assertIsInstance(s, Site)
        s.delete()
        with self.assertRaises(ObjectDoesNotExist):
            Site.objects.get_current()