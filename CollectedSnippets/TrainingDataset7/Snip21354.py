def test_filter_with_join(self):
        # F Expressions can also span joins
        Company.objects.update(point_of_contact=F("ceo"))
        c = Company.objects.first()
        c.point_of_contact = Employee.objects.create(
            firstname="Guido", lastname="van Rossum"
        )
        c.save()

        self.assertQuerySetEqual(
            Company.objects.filter(ceo__firstname=F("point_of_contact__firstname")),
            ["Foobar Ltd.", "Test GmbH"],
            lambda c: c.name,
            ordered=False,
        )

        Company.objects.exclude(ceo__firstname=F("point_of_contact__firstname")).update(
            name="foo"
        )
        self.assertEqual(
            Company.objects.exclude(ceo__firstname=F("point_of_contact__firstname"))
            .get()
            .name,
            "foo",
        )

        msg = "Joined field references are not permitted in this query"
        with self.assertRaisesMessage(FieldError, msg):
            Company.objects.exclude(
                ceo__firstname=F("point_of_contact__firstname")
            ).update(name=F("point_of_contact__lastname"))