def test_constructor_with_id(self):
        """Test DeltaGenerator() with an id."""
        cursor = LockedCursor(root_container=RootContainer.MAIN, index=1234)
        dg = DeltaGenerator(root_container=RootContainer.MAIN, cursor=cursor)
        self.assertTrue(dg._cursor.is_locked)
        self.assertEqual(dg._cursor.index, 1234)