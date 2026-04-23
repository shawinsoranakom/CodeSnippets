def test_fast_delete_inheritance(self):
        c = Child.objects.create()
        p = Parent.objects.create()
        # 1 for self, 1 for parent
        self.assertNumQueries(2, c.delete)
        self.assertFalse(Child.objects.exists())
        self.assertEqual(Parent.objects.count(), 1)
        self.assertEqual(Parent.objects.filter(pk=p.pk).count(), 1)
        # 1 for self delete, 1 for fast delete of empty "child" qs.
        self.assertNumQueries(2, p.delete)
        self.assertFalse(Parent.objects.exists())
        # 1 for self delete, 1 for fast delete of empty "child" qs.
        c = Child.objects.create()
        p = c.parent_ptr
        self.assertNumQueries(2, p.delete)
        self.assertFalse(Parent.objects.exists())
        self.assertFalse(Child.objects.exists())