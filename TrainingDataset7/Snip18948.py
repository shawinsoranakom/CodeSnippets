def test_refresh_fk(self):
        s1 = SelfRef.objects.create()
        s2 = SelfRef.objects.create()
        s3 = SelfRef.objects.create(selfref=s1)
        s3_copy = SelfRef.objects.get(pk=s3.pk)
        s3_copy.selfref.touched = True
        s3.selfref = s2
        s3.save()
        with self.assertNumQueries(1):
            s3_copy.refresh_from_db()
        with self.assertNumQueries(1):
            # The old related instance was thrown away (the selfref_id has
            # changed). It needs to be reloaded on access, so one query
            # executed.
            self.assertFalse(hasattr(s3_copy.selfref, "touched"))
            self.assertEqual(s3_copy.selfref, s2)