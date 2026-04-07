def test_deconstruct_from_queryset(self):
        mgr = DeconstructibleCustomManager("a", "b")
        as_manager, mgr_path, qs_path, args, kwargs = mgr.deconstruct()
        self.assertFalse(as_manager)
        self.assertEqual(
            mgr_path, "custom_managers.models.DeconstructibleCustomManager"
        )
        self.assertEqual(
            args,
            (
                "a",
                "b",
            ),
        )
        self.assertEqual(kwargs, {})

        mgr = DeconstructibleCustomManager("x", "y", c=3, d=4)
        as_manager, mgr_path, qs_path, args, kwargs = mgr.deconstruct()
        self.assertFalse(as_manager)
        self.assertEqual(
            mgr_path, "custom_managers.models.DeconstructibleCustomManager"
        )
        self.assertEqual(
            args,
            (
                "x",
                "y",
            ),
        )
        self.assertEqual(kwargs, {"c": 3, "d": 4})