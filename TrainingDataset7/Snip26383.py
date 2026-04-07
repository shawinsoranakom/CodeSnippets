def test_save_nullable_fk_after_parent(self):
        parent = Parent()
        child = ChildNullableParent(parent=parent)
        parent.save()
        child.save()
        child.refresh_from_db()
        self.assertEqual(child.parent, parent)