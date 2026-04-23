def test_setvalue(self):
        a = create_a("setvalue")
        a.setvalue.delete()
        a = A.objects.get(pk=a.pk)
        self.assertEqual(self.DEFAULT, a.setvalue.pk)