def test_unsupported_lookup_reverse_foreign_key_custom_lookups(self):
        msg = (
            "Unsupported lookup 'abspl' for ManyToOneRel or join on the field not "
            "permitted, perhaps you meant abspk?"
        )
        fk_field = Article._meta.get_field("author")
        with self.assertRaisesMessage(FieldError, msg):
            with register_lookup(fk_field, Abs, lookup_name="abspk"):
                Author.objects.filter(article__abspl=2)