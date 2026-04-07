def test_unsupported_lookup_reverse_foreign_key(self):
        msg = (
            "Unsupported lookup 'title' for ManyToOneRel or join on the field not "
            "permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Author.objects.filter(article__title="Article 1")