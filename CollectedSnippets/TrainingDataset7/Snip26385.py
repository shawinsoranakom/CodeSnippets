def test_save_fk_after_parent_with_non_numeric_pk_set_on_child(self):
        parent = ParentStringPrimaryKey()
        child = ChildStringPrimaryKeyParent(parent=parent)
        child.parent.name = "jeff"
        parent.save()
        child.save()
        child.refresh_from_db()
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.parent_id, parent.name)