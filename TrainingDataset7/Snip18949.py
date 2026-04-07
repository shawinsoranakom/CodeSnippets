def test_refresh_null_fk(self):
        s1 = SelfRef.objects.create()
        s2 = SelfRef.objects.create(selfref=s1)
        s2.selfref = None
        s2.refresh_from_db()
        self.assertEqual(s2.selfref, s1)