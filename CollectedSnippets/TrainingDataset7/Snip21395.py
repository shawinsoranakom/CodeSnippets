def test_annotation_with_nested_outerref(self):
        self.gmbh.point_of_contact = Employee.objects.get(lastname="Meyer")
        self.gmbh.save()
        inner = Employee.objects.annotate(
            outer_lastname=OuterRef(OuterRef("lastname")),
        ).filter(lastname__startswith=Left("outer_lastname", 1))
        qs = Employee.objects.annotate(
            ceo_company=Subquery(
                Company.objects.filter(
                    point_of_contact__in=inner,
                    ceo__pk=OuterRef("pk"),
                ).values("name"),
            ),
        ).filter(ceo_company__isnull=False)
        self.assertEqual(qs.get().ceo_company, "Test GmbH")