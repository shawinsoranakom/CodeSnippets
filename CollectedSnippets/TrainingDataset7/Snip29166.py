def test_migrate_selection(self):
        "Synchronization behavior is predictable"

        self.assertTrue(router.allow_migrate_model("default", User))
        self.assertTrue(router.allow_migrate_model("default", Book))

        self.assertTrue(router.allow_migrate_model("other", User))
        self.assertTrue(router.allow_migrate_model("other", Book))

        with override_settings(DATABASE_ROUTERS=[TestRouter(), AuthRouter()]):
            # Add the auth router to the chain. TestRouter is a universal
            # synchronizer, so it should have no effect.
            self.assertTrue(router.allow_migrate_model("default", User))
            self.assertTrue(router.allow_migrate_model("default", Book))

            self.assertTrue(router.allow_migrate_model("other", User))
            self.assertTrue(router.allow_migrate_model("other", Book))

        with override_settings(DATABASE_ROUTERS=[AuthRouter(), TestRouter()]):
            # Now check what happens if the router order is reversed.
            self.assertFalse(router.allow_migrate_model("default", User))
            self.assertTrue(router.allow_migrate_model("default", Book))

            self.assertTrue(router.allow_migrate_model("other", User))
            self.assertTrue(router.allow_migrate_model("other", Book))