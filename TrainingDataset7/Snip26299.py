def test_regress_3871(self):
        related = RelatedModel.objects.create()

        relation = RelationModel()
        relation.fk = related
        relation.gfk = related
        relation.save()
        relation.m2m.add(related)

        t = Template(
            "{{ related.test_fk.all.0 }}{{ related.test_gfk.all.0 }}"
            "{{ related.test_m2m.all.0 }}"
        )

        self.assertEqual(
            t.render(Context({"related": related})),
            "".join([str(relation.pk)] * 3),
        )