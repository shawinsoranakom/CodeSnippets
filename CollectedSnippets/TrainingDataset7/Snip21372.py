def test_subquery(self):
        Company.objects.filter(name="Example Inc.").update(
            point_of_contact=Employee.objects.get(firstname="Joe", lastname="Smith"),
            ceo=self.max,
        )
        Employee.objects.create(firstname="Bob", lastname="Brown", salary=40)
        qs = (
            Employee.objects.annotate(
                is_point_of_contact=Exists(
                    Company.objects.filter(point_of_contact=OuterRef("pk"))
                ),
                is_not_point_of_contact=~Exists(
                    Company.objects.filter(point_of_contact=OuterRef("pk"))
                ),
                is_ceo_of_small_company=Exists(
                    Company.objects.filter(num_employees__lt=200, ceo=OuterRef("pk"))
                ),
                is_ceo_small_2=~~Exists(
                    Company.objects.filter(num_employees__lt=200, ceo=OuterRef("pk"))
                ),
                largest_company=Subquery(
                    Company.objects.order_by("-num_employees")
                    .filter(Q(ceo=OuterRef("pk")) | Q(point_of_contact=OuterRef("pk")))
                    .values("name")[:1],
                    output_field=CharField(),
                ),
            )
            .values(
                "firstname",
                "is_point_of_contact",
                "is_not_point_of_contact",
                "is_ceo_of_small_company",
                "is_ceo_small_2",
                "largest_company",
            )
            .order_by("firstname")
        )

        results = list(qs)
        # Could use Coalesce(subq, Value('')) instead except for the bug in
        # oracledb mentioned in #23843.
        bob = results[0]
        if (
            bob["largest_company"] == ""
            and connection.features.interprets_empty_strings_as_nulls
        ):
            bob["largest_company"] = None

        self.assertEqual(
            results,
            [
                {
                    "firstname": "Bob",
                    "is_point_of_contact": False,
                    "is_not_point_of_contact": True,
                    "is_ceo_of_small_company": False,
                    "is_ceo_small_2": False,
                    "largest_company": None,
                },
                {
                    "firstname": "Frank",
                    "is_point_of_contact": False,
                    "is_not_point_of_contact": True,
                    "is_ceo_of_small_company": True,
                    "is_ceo_small_2": True,
                    "largest_company": "Foobar Ltd.",
                },
                {
                    "firstname": "Joe",
                    "is_point_of_contact": True,
                    "is_not_point_of_contact": False,
                    "is_ceo_of_small_company": False,
                    "is_ceo_small_2": False,
                    "largest_company": "Example Inc.",
                },
                {
                    "firstname": "Max",
                    "is_point_of_contact": False,
                    "is_not_point_of_contact": True,
                    "is_ceo_of_small_company": True,
                    "is_ceo_small_2": True,
                    "largest_company": "Example Inc.",
                },
            ],
        )
        # A less elegant way to write the same query: this uses a LEFT OUTER
        # JOIN and an IS NULL, inside a WHERE NOT IN which is probably less
        # efficient than EXISTS.
        self.assertCountEqual(
            qs.filter(is_point_of_contact=True).values("pk"),
            Employee.objects.exclude(company_point_of_contact_set=None).values("pk"),
        )