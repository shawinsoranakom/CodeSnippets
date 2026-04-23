def test_o2o_setnull(self):
        a = create_a("o2o_setnull")
        a.o2o_setnull.delete()
        a = A.objects.get(pk=a.pk)
        self.assertIsNone(a.o2o_setnull)