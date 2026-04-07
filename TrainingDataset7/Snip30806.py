def test_exclude_m2m_through(self):
        alex = Person.objects.get_or_create(name="Alex")[0]
        jane = Person.objects.get_or_create(name="Jane")[0]

        oracle = Company.objects.get_or_create(name="Oracle")[0]
        google = Company.objects.get_or_create(name="Google")[0]
        microsoft = Company.objects.get_or_create(name="Microsoft")[0]
        intel = Company.objects.get_or_create(name="Intel")[0]

        def employ(employer, employee, title):
            Employment.objects.get_or_create(
                employee=employee, employer=employer, title=title
            )

        employ(oracle, alex, "Engineer")
        employ(oracle, alex, "Developer")
        employ(google, alex, "Engineer")
        employ(google, alex, "Manager")
        employ(microsoft, alex, "Manager")
        employ(intel, alex, "Manager")

        employ(microsoft, jane, "Developer")
        employ(intel, jane, "Manager")

        alex_tech_employers = (
            alex.employers.filter(employment__title__in=("Engineer", "Developer"))
            .distinct()
            .order_by("name")
        )
        self.assertSequenceEqual(alex_tech_employers, [google, oracle])

        alex_nontech_employers = (
            alex.employers.exclude(employment__title__in=("Engineer", "Developer"))
            .distinct()
            .order_by("name")
        )
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(alex_nontech_employers, [google, intel, microsoft])
        sql = ctx.captured_queries[0]["sql"]
        # Company's ID should appear in SELECT and INNER JOIN, not in EXISTS as
        # the outer query reference is not necessary when an alias is reused.
        company_id = "%s.%s" % (
            connection.ops.quote_name(Company._meta.db_table),
            connection.ops.quote_name(Company._meta.get_field("id").column),
        )
        self.assertEqual(sql.count(company_id), 2)