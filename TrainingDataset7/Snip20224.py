def test_deconstruct_default(self):
        mgr = models.Manager()
        as_manager, mgr_path, qs_path, args, kwargs = mgr.deconstruct()
        self.assertFalse(as_manager)
        self.assertEqual(mgr_path, "django.db.models.manager.Manager")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})