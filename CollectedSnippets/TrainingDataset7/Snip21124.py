def test_delete_with_keeping_parents_relationships(self):
        child = RChild.objects.create()
        parent_id = child.r_ptr_id
        parent_referent_id = S.objects.create(r=child.r_ptr).pk
        child.delete(keep_parents=True)
        self.assertFalse(RChild.objects.filter(id=child.id).exists())
        self.assertTrue(R.objects.filter(id=parent_id).exists())
        self.assertTrue(S.objects.filter(pk=parent_referent_id).exists())

        childchild = RChildChild.objects.create()
        parent_id = childchild.rchild_ptr.r_ptr_id
        child_id = childchild.rchild_ptr_id
        parent_referent_id = S.objects.create(r=childchild.rchild_ptr.r_ptr).pk
        childchild.delete(keep_parents=True)
        self.assertFalse(RChildChild.objects.filter(id=childchild.id).exists())
        self.assertTrue(RChild.objects.filter(id=child_id).exists())
        self.assertTrue(R.objects.filter(id=parent_id).exists())
        self.assertTrue(S.objects.filter(pk=parent_referent_id).exists())