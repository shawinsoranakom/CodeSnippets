def test_values_wrong_annotation(self):
        expected_message = (
            "Cannot resolve keyword 'annotation_typo' into field. Choices are: %s"
        )
        article_fields = ", ".join(
            ["annotation"] + sorted(get_field_names_from_opts(Book._meta))
        )
        with self.assertRaisesMessage(FieldError, expected_message % article_fields):
            Book.objects.annotate(annotation=Value(1)).values_list("annotation_typo")