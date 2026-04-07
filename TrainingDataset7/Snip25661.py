def test_multilevel_reverse_fk_cyclic_select_related(self):
        with self.assertNumQueries(3):
            p = list(
                PoolStyle.objects.annotate(
                    tournament_pool=FilteredRelation("pool__tournament__pool"),
                ).select_related("tournament_pool", "tournament_pool__tournament")
            )
            self.assertEqual(p[0].tournament_pool.tournament, p[0].pool.tournament)