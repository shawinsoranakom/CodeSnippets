def test_reverse_relation_pk(self):
        """
        The correct column name is used for the primary key on the
        originating model of a query. See #12664.
        """
        p = Person.objects.create(account=23, name="Chef")
        Address.objects.create(
            street="123 Anywhere Place",
            city="Conifer",
            state="CO",
            zipcode="80433",
            content_object=p,
        )

        qs = Person.objects.filter(addresses__zipcode="80433")
        self.assertEqual(1, qs.count())
        self.assertEqual("Chef", qs[0].name)