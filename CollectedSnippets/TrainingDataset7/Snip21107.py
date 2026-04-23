def test_restrict_path_cascade_direct(self):
        a = create_a("restrict")
        a.restrict.p = P.objects.create()
        a.restrict.save()
        a.cascade_p = a.restrict.p
        a.save()
        a.restrict.p.delete()
        self.assertFalse(A.objects.filter(name="restrict").exists())
        self.assertFalse(R.objects.filter(pk=a.restrict_id).exists())