def test_cascade_from_parent(self):
        a = create_a("child")
        R.objects.get(pk=a.child_id).delete()
        self.assertFalse(A.objects.filter(name="child").exists())
        self.assertFalse(RChild.objects.filter(pk=a.child_id).exists())