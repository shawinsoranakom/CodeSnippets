def tearDown(self):
        site.unregister(Song)
        if site.is_registered(Band):
            site.unregister(Band)