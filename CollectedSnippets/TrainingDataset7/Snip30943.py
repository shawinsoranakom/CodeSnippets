def test_pickle_filteredrelation_m2m(self):
        group = Group.objects.create(name="group")
        m2mmodel = M2MModel.objects.create(added=datetime.date(2020, 1, 1))
        m2mmodel.groups.add(group)
        groups = Group.objects.annotate(
            first_m2mmodels=models.FilteredRelation(
                "m2mmodel",
                condition=models.Q(m2mmodel__added__year=2020),
            ),
        ).annotate(count_groups=models.Count("first_m2mmodels__groups"))
        groups_query = pickle.loads(pickle.dumps(groups.query))
        groups = Group.objects.all()
        groups.query = groups_query
        self.assertEqual(groups.get().count_groups, 1)