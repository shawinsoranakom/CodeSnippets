def test_override_database_routers(self):
        """
        Overriding DATABASE_ROUTERS should update the base router.
        """
        test_routers = [object()]
        with self.settings(DATABASE_ROUTERS=test_routers):
            self.assertEqual(router.routers, test_routers)