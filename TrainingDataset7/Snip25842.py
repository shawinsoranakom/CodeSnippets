def test_nonfield_lookups(self):
        """
        A lookup query containing non-fields raises the proper exception.
        """
        msg = (
            "Unsupported lookup 'blahblah' for CharField or join on the field not "
            "permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.filter(headline__blahblah=99)
        msg = (
            "Unsupported lookup 'blahblah__exact' for CharField or join "
            "on the field not permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.filter(headline__blahblah__exact=99)
        msg = (
            "Cannot resolve keyword 'blahblah' into field. Choices are: "
            "author, author_id, headline, id, pub_date, slug, tag"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.filter(blahblah=99)