def test_auto(self):
        a = create_a("auto")
        a.auto.delete()
        self.assertFalse(A.objects.filter(name="auto").exists())