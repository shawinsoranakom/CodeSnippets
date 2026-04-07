def test_setdefault(self):
        a = create_a("setdefault")
        a.setdefault.delete()
        a = A.objects.get(pk=a.pk)
        self.assertEqual(self.DEFAULT, a.setdefault.pk)