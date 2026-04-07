def test_prefetch_nullable(self):
        # One for main employee, one for boss, one for serfs
        with self.assertNumQueries(3):
            qs = Employee.objects.prefetch_related("boss__serfs")
            co_serfs = [
                list(e.boss.serfs.all()) if e.boss is not None else [] for e in qs
            ]

        qs2 = Employee.objects.all()
        co_serfs2 = [
            list(e.boss.serfs.all()) if e.boss is not None else [] for e in qs2
        ]

        self.assertEqual(co_serfs, co_serfs2)