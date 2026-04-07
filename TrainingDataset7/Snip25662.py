def test_multilevel_reverse_fk_select_related(self):
        with self.assertNumQueries(2):
            p = list(
                Tournament.objects.filter(id=self.t2.id)
                .annotate(
                    style=FilteredRelation("pool__another_style"),
                )
                .select_related("style")
            )
            self.assertEqual(p[0].style.another_pool, self.p3)