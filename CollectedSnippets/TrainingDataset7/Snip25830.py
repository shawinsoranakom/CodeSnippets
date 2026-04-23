def test_unsupported_lookups(self):
        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'starts' for CharField or join on the field "
            "not permitted, perhaps you meant startswith or istartswith?",
        ):
            Article.objects.filter(headline__starts="Article")

        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'is_null' for DateTimeField or join on the field "
            "not permitted, perhaps you meant isnull?",
        ):
            Article.objects.filter(pub_date__is_null=True)

        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'gobbledygook' for DateTimeField or join on the field "
            "not permitted.",
        ):
            Article.objects.filter(pub_date__gobbledygook="blahblah")

        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'gt__foo' for DateTimeField or join on the field "
            "not permitted, perhaps you meant gt or gte?",
        ):
            Article.objects.filter(pub_date__gt__foo="blahblah")

        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'gt__' for DateTimeField or join on the field "
            "not permitted, perhaps you meant gt or gte?",
        ):
            Article.objects.filter(pub_date__gt__="blahblah")

        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'gt__lt' for DateTimeField or join on the field "
            "not permitted, perhaps you meant gt or gte?",
        ):
            Article.objects.filter(pub_date__gt__lt="blahblah")

        with self.assertRaisesMessage(
            FieldError,
            "Unsupported lookup 'gt__lt__foo' for DateTimeField or join"
            " on the field not permitted, perhaps you meant gt or gte?",
        ):
            Article.objects.filter(pub_date__gt__lt__foo="blahblah")