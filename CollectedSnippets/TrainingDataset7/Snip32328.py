def test_no_site_id(self):
        """
        #24488 - The pk should default to 1 if no ``SITE_ID`` is configured.
        """
        del settings.SITE_ID
        create_default_site(self.app_config, verbosity=0)
        self.assertEqual(Site.objects.get().pk, 1)