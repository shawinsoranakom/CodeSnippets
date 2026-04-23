def test_multi_db(self):
        create_default_site(self.app_config, using="default", verbosity=0)
        create_default_site(self.app_config, using="other", verbosity=0)
        self.assertTrue(Site.objects.using("default").exists())
        self.assertTrue(Site.objects.using("other").exists())