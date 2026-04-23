def test_unavailable_site_model(self):
        """
        #24075 - A Site shouldn't be created if the model isn't available.
        """
        apps = Apps()
        create_default_site(self.app_config, verbosity=0, apps=apps)
        self.assertFalse(Site.objects.exists())