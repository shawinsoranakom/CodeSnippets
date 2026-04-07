def test_deconstruct_as_manager(self):
        mgr = CustomQuerySet.as_manager()
        as_manager, mgr_path, qs_path, args, kwargs = mgr.deconstruct()
        self.assertTrue(as_manager)
        self.assertEqual(qs_path, "custom_managers.models.CustomQuerySet")