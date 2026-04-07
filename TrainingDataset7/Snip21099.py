def test_cascade_from_child(self):
        a = create_a("child")
        a.child.delete()
        self.assertFalse(A.objects.filter(name="child").exists())
        self.assertFalse(R.objects.filter(pk=a.child_id).exists())