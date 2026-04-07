def test_custom_site_id(self):
        """
        #23945 - The configured ``SITE_ID`` should be respected.
        """
        create_default_site(self.app_config, verbosity=0)
        self.assertEqual(Site.objects.get().pk, 35696)