def test_partial_router(self):
        "A router can choose to implement a subset of methods"
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        # First check the baseline behavior.

        self.assertEqual(router.db_for_read(User), "other")
        self.assertEqual(router.db_for_read(Book), "other")

        self.assertEqual(router.db_for_write(User), "default")
        self.assertEqual(router.db_for_write(Book), "default")

        self.assertTrue(router.allow_relation(dive, dive))

        self.assertTrue(router.allow_migrate_model("default", User))
        self.assertTrue(router.allow_migrate_model("default", Book))

        with override_settings(
            DATABASE_ROUTERS=[WriteRouter(), AuthRouter(), TestRouter()]
        ):
            self.assertEqual(router.db_for_read(User), "default")
            self.assertEqual(router.db_for_read(Book), "other")

            self.assertEqual(router.db_for_write(User), "writer")
            self.assertEqual(router.db_for_write(Book), "writer")

            self.assertTrue(router.allow_relation(dive, dive))

            self.assertFalse(router.allow_migrate_model("default", User))
            self.assertTrue(router.allow_migrate_model("default", Book))