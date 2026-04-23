def test_nested_outerref_with_function(self):
        self.gmbh.point_of_contact = Employee.objects.get(lastname="Meyer")
        self.gmbh.save()
        inner = Employee.objects.filter(
            lastname__startswith=Left(OuterRef(OuterRef("lastname")), 1),
        )
        qs = Employee.objects.annotate(
            ceo_company=Subquery(
                Company.objects.filter(
                    point_of_contact__in=inner,
                    ceo__pk=OuterRef("pk"),
                ).values("name"),
            ),
        ).filter(ceo_company__isnull=False)
        self.assertEqual(qs.get().ceo_company, "Test GmbH")