def test_multi_db_with_router(self):
        """
        #16353, #16828 - The default site creation should respect db routing.
        """
        create_default_site(self.app_config, using="default", verbosity=0)
        create_default_site(self.app_config, using="other", verbosity=0)
        self.assertFalse(Site.objects.using("default").exists())
        self.assertTrue(Site.objects.using("other").exists())