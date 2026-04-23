def test_setnull(self):
        a = create_a("setnull")
        a.setnull.delete()
        a = A.objects.get(pk=a.pk)
        self.assertIsNone(a.setnull)