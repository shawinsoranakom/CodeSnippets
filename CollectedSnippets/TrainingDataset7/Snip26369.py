def test_assign_fk_id_none(self):
        parent = Parent.objects.create(name="jeff")
        child = Child.objects.create(name="frank", parent=parent)
        parent.bestchild = child
        parent.save()
        parent.bestchild_id = None
        parent.save()
        self.assertIsNone(parent.bestchild_id)
        self.assertFalse(Parent.bestchild.is_cached(parent))
        self.assertIsNone(parent.bestchild)
        self.assertTrue(Parent.bestchild.is_cached(parent))