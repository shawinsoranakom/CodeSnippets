def test_annotation(self):
        # Annotations get combined with extra select clauses
        obj = (
            Book.objects.annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"manufacture_cost": "price * .5"})
            .get(pk=self.b2.pk)
        )
        self.assertObjectAttrs(
            obj,
            contact_id=self.a3.id,
            isbn="067232959",
            mean_auth_age=45.0,
            name="Sams Teach Yourself Django in 24 Hours",
            pages=528,
            price=Decimal("23.09"),
            pubdate=datetime.date(2008, 3, 3),
            publisher_id=self.p2.id,
            rating=3.0,
        )
        # Different DB backends return different types for the extra select
        # computation
        self.assertIn(obj.manufacture_cost, (11.545, Decimal("11.545")))

        # Order of the annotate/extra in the query doesn't matter
        obj = (
            Book.objects.extra(select={"manufacture_cost": "price * .5"})
            .annotate(mean_auth_age=Avg("authors__age"))
            .get(pk=self.b2.pk)
        )
        self.assertObjectAttrs(
            obj,
            contact_id=self.a3.id,
            isbn="067232959",
            mean_auth_age=45.0,
            name="Sams Teach Yourself Django in 24 Hours",
            pages=528,
            price=Decimal("23.09"),
            pubdate=datetime.date(2008, 3, 3),
            publisher_id=self.p2.id,
            rating=3.0,
        )
        # Different DB backends return different types for the extra select
        # computation
        self.assertIn(obj.manufacture_cost, (11.545, Decimal("11.545")))

        # Values queries can be combined with annotate and extra
        obj = (
            Book.objects.annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"manufacture_cost": "price * .5"})
            .values()
            .get(pk=self.b2.pk)
        )
        manufacture_cost = obj["manufacture_cost"]
        self.assertIn(manufacture_cost, (11.545, Decimal("11.545")))
        del obj["manufacture_cost"]
        self.assertEqual(
            obj,
            {
                "id": self.b2.id,
                "contact_id": self.a3.id,
                "isbn": "067232959",
                "mean_auth_age": 45.0,
                "name": "Sams Teach Yourself Django in 24 Hours",
                "pages": 528,
                "price": Decimal("23.09"),
                "pubdate": datetime.date(2008, 3, 3),
                "publisher_id": self.p2.id,
                "rating": 3.0,
            },
        )

        # The order of the (empty) values, annotate and extra clauses doesn't
        # matter
        obj = (
            Book.objects.values()
            .annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"manufacture_cost": "price * .5"})
            .get(pk=self.b2.pk)
        )
        manufacture_cost = obj["manufacture_cost"]
        self.assertIn(manufacture_cost, (11.545, Decimal("11.545")))
        del obj["manufacture_cost"]
        self.assertEqual(
            obj,
            {
                "id": self.b2.id,
                "contact_id": self.a3.id,
                "isbn": "067232959",
                "mean_auth_age": 45.0,
                "name": "Sams Teach Yourself Django in 24 Hours",
                "pages": 528,
                "price": Decimal("23.09"),
                "pubdate": datetime.date(2008, 3, 3),
                "publisher_id": self.p2.id,
                "rating": 3.0,
            },
        )

        # If the annotation precedes the values clause, it won't be included
        # unless it is explicitly named
        obj = (
            Book.objects.annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"price_per_page": "price / pages"})
            .values("name")
            .get(pk=self.b1.pk)
        )
        self.assertEqual(
            obj,
            {
                "name": "The Definitive Guide to Django: Web Development Done Right",
            },
        )

        obj = (
            Book.objects.annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"price_per_page": "price / pages"})
            .values("name", "mean_auth_age")
            .get(pk=self.b1.pk)
        )
        self.assertEqual(
            obj,
            {
                "mean_auth_age": 34.5,
                "name": "The Definitive Guide to Django: Web Development Done Right",
            },
        )

        # If an annotation isn't included in the values, it can still be used
        # in a filter
        qs = (
            Book.objects.annotate(n_authors=Count("authors"))
            .values("name")
            .filter(n_authors__gt=2)
        )
        self.assertSequenceEqual(
            qs,
            [{"name": "Python Web Development with Django"}],
        )

        # The annotations are added to values output if values() precedes
        # annotate()
        obj = (
            Book.objects.values("name")
            .annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"price_per_page": "price / pages"})
            .get(pk=self.b1.pk)
        )
        self.assertEqual(
            obj,
            {
                "mean_auth_age": 34.5,
                "name": "The Definitive Guide to Django: Web Development Done Right",
            },
        )

        # All of the objects are getting counted (allow_nulls) and that values
        # respects the amount of objects
        self.assertEqual(len(Author.objects.annotate(Avg("friends__age")).values()), 9)

        # Consecutive calls to annotate accumulate in the query
        qs = (
            Book.objects.values("price")
            .annotate(oldest=Max("authors__age"))
            .order_by("oldest", "price")
            .annotate(Max("publisher__num_awards"))
        )
        self.assertSequenceEqual(
            qs,
            [
                {"price": Decimal("30"), "oldest": 35, "publisher__num_awards__max": 3},
                {
                    "price": Decimal("29.69"),
                    "oldest": 37,
                    "publisher__num_awards__max": 7,
                },
                {
                    "price": Decimal("23.09"),
                    "oldest": 45,
                    "publisher__num_awards__max": 1,
                },
                {"price": Decimal("75"), "oldest": 57, "publisher__num_awards__max": 9},
                {
                    "price": Decimal("82.8"),
                    "oldest": 57,
                    "publisher__num_awards__max": 7,
                },
            ],
        )