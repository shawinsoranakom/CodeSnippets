def test_signal(self):
        """
        #23641 - Sending the ``post_migrate`` signal triggers creation of the
        default site.
        """
        post_migrate.send(
            sender=self.app_config, app_config=self.app_config, verbosity=0
        )
        self.assertTrue(Site.objects.exists())