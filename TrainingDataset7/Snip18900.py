def test_save_parent_primary_with_default(self):
        # An UPDATE attempt is skipped when an inherited primary key has
        # default.
        with self.assertNumQueries(2):
            ChildPrimaryKeyWithDefault().save()