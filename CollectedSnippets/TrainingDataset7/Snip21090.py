def test_cascade(self):
        a = create_a("cascade")
        a.cascade.delete()
        self.assertFalse(A.objects.filter(name="cascade").exists())