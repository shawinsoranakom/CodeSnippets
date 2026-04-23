def test_cascade_nullable(self):
        a = create_a("cascade_nullable")
        a.cascade_nullable.delete()
        self.assertFalse(A.objects.filter(name="cascade_nullable").exists())