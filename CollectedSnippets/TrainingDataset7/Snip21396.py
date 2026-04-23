def test_annotation_with_deeply_nested_outerref(self):
        bob = Employee.objects.create(firstname="Bob", based_in_eu=True)
        self.max.manager = Manager.objects.create(name="Rock", secretary=bob)
        self.max.save()
        qs = Employee.objects.filter(
            Exists(
                Manager.objects.filter(
                    Exists(
                        Employee.objects.filter(
                            pk=OuterRef("secretary__pk"),
                        )
                        .annotate(
                            secretary_based_in_eu=OuterRef(OuterRef("based_in_eu"))
                        )
                        .filter(
                            Exists(
                                Company.objects.filter(
                                    # Inner OuterRef refers to an outer
                                    # OuterRef (not ResolvedOuterRef).
                                    based_in_eu=OuterRef("secretary_based_in_eu")
                                )
                            )
                        )
                    ),
                    secretary__pk=OuterRef("pk"),
                )
            )
        )
        self.assertEqual(qs.get(), bob)