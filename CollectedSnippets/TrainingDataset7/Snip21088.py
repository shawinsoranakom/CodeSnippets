def test_setdefault_none(self):
        a = create_a("setdefault_none")
        a.setdefault_none.delete()
        a = A.objects.get(pk=a.pk)
        self.assertIsNone(a.setdefault_none)