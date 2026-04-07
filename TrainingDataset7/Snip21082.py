def test_auto_nullable(self):
        a = create_a("auto_nullable")
        a.auto_nullable.delete()
        self.assertFalse(A.objects.filter(name="auto_nullable").exists())