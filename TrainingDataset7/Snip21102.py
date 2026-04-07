def test_setnull_from_parent(self):
        a = create_a("child_setnull")
        R.objects.get(pk=a.child_setnull_id).delete()
        self.assertFalse(RChild.objects.filter(pk=a.child_setnull_id).exists())

        a = A.objects.get(pk=a.pk)
        self.assertIsNone(a.child_setnull)