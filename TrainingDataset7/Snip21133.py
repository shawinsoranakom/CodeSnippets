def test_fast_delete_revm2m(self):
        t = M2MTo.objects.create()
        f = M2MFrom.objects.create()
        f.m2m.add(t)
        # 1 to delete t, 1 to fast-delete t's m_set
        self.assertNumQueries(2, f.delete)