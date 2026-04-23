def test_traverse_nullable(self):
        # Because we use select_related() for 'boss', it doesn't need to be
        # prefetched, but we can still traverse it although it contains some
        # nulls
        with self.assertNumQueries(2):
            qs = Employee.objects.select_related("boss").prefetch_related("boss__serfs")
            co_serfs = [
                list(e.boss.serfs.all()) if e.boss is not None else [] for e in qs
            ]

        qs2 = Employee.objects.select_related("boss")
        co_serfs2 = [
            list(e.boss.serfs.all()) if e.boss is not None else [] for e in qs2
        ]

        self.assertEqual(co_serfs, co_serfs2)