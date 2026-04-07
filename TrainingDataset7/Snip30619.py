def test_ticket8439(self):
        # Complex combinations of conjunctions, disjunctions and nullable
        # relations.
        self.assertSequenceEqual(
            Author.objects.filter(
                Q(item__note__extrainfo=self.e2) | Q(report=self.r1, name="xyz")
            ),
            [self.a2],
        )
        self.assertSequenceEqual(
            Author.objects.filter(
                Q(report=self.r1, name="xyz") | Q(item__note__extrainfo=self.e2)
            ),
            [self.a2],
        )
        self.assertSequenceEqual(
            Annotation.objects.filter(
                Q(tag__parent=self.t1) | Q(notes__note="n1", name="a1")
            ),
            [self.ann1],
        )
        xx = ExtraInfo.objects.create(info="xx", note=self.n3)
        self.assertSequenceEqual(
            Note.objects.filter(Q(extrainfo__author=self.a1) | Q(extrainfo=xx)),
            [self.n1, self.n3],
        )
        q = Note.objects.filter(Q(extrainfo__author=self.a1) | Q(extrainfo=xx)).query
        self.assertEqual(
            len(
                [
                    x
                    for x in q.alias_map.values()
                    if x.join_type == LOUTER and q.alias_refcount[x.table_alias]
                ]
            ),
            1,
        )