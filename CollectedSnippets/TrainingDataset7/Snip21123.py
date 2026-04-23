def test_delete_with_keeping_parents(self):
        child = RChild.objects.create()
        parent_id = child.r_ptr_id
        child.delete(keep_parents=True)
        self.assertFalse(RChild.objects.filter(id=child.id).exists())
        self.assertTrue(R.objects.filter(id=parent_id).exists())