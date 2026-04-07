def test_aggregation_with_generic_reverse_relation(self):
        """
        Regression test for #10870:  Aggregates with joins ignore extra
        filters provided by setup_joins

        tests aggregations with generic reverse relations
        """
        django_book = Book.objects.get(name="Practical Django Projects")
        ItemTag.objects.create(
            object_id=django_book.id,
            tag="intermediate",
            content_type=ContentType.objects.get_for_model(django_book),
        )
        ItemTag.objects.create(
            object_id=django_book.id,
            tag="django",
            content_type=ContentType.objects.get_for_model(django_book),
        )
        # Assign a tag to model with same PK as the book above. If the JOIN
        # used in aggregation doesn't have content type as part of the
        # condition the annotation will also count the 'hi mom' tag for b.
        wmpk = WithManualPK.objects.create(id=django_book.pk)
        ItemTag.objects.create(
            object_id=wmpk.id,
            tag="hi mom",
            content_type=ContentType.objects.get_for_model(wmpk),
        )
        ai_book = Book.objects.get(
            name__startswith="Paradigms of Artificial Intelligence"
        )
        ItemTag.objects.create(
            object_id=ai_book.id,
            tag="intermediate",
            content_type=ContentType.objects.get_for_model(ai_book),
        )

        self.assertEqual(Book.objects.aggregate(Count("tags")), {"tags__count": 3})
        results = Book.objects.annotate(Count("tags")).order_by("-tags__count", "name")
        self.assertEqual(
            [(b.name, b.tags__count) for b in results],
            [
                ("Practical Django Projects", 2),
                (
                    "Paradigms of Artificial Intelligence Programming: Case Studies in "
                    "Common Lisp",
                    1,
                ),
                ("Artificial Intelligence: A Modern Approach", 0),
                ("Python Web Development with Django", 0),
                ("Sams Teach Yourself Django in 24 Hours", 0),
                ("The Definitive Guide to Django: Web Development Done Right", 0),
            ],
        )