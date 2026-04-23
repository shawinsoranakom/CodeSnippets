def test_field_error(self):
        # Bad field requests in aggregates are caught and reported
        msg = (
            "Cannot resolve keyword 'foo' into field. Choices are: authors, "
            "contact, contact_id, hardbackbook, id, isbn, name, pages, price, "
            "pubdate, publisher, publisher_id, rating, store, tags"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Book.objects.aggregate(num_authors=Count("foo"))

        with self.assertRaisesMessage(FieldError, msg):
            Book.objects.annotate(num_authors=Count("foo"))

        msg = (
            "Cannot resolve keyword 'foo' into field. Choices are: authors, "
            "contact, contact_id, hardbackbook, id, isbn, name, num_authors, "
            "pages, price, pubdate, publisher, publisher_id, rating, store, tags"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Book.objects.annotate(num_authors=Count("authors__id")).aggregate(
                Max("foo")
            )