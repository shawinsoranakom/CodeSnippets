def test_assign_fk_id_value(self):
        parent = Parent.objects.create(name="jeff")
        child1 = Child.objects.create(name="frank", parent=parent)
        child2 = Child.objects.create(name="randy", parent=parent)
        parent.bestchild = child1
        parent.save()
        parent.bestchild_id = child2.pk
        parent.save()
        self.assertEqual(parent.bestchild_id, child2.pk)
        self.assertFalse(Parent.bestchild.is_cached(parent))
        self.assertEqual(parent.bestchild, child2)
        self.assertTrue(Parent.bestchild.is_cached(parent))
        # Reassigning the same value doesn't clear cached instance.
        parent.bestchild_id = child2.pk
        self.assertTrue(Parent.bestchild.is_cached(parent))