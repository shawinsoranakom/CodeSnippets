def test_save_nullable_fk_after_parent_with_to_field(self):
        parent = Parent(name="jeff")
        child = ToFieldChild(parent=parent)
        parent.save()
        child.save()
        child.refresh_from_db()
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.parent_id, parent.name)