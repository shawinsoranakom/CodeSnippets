def test_values_list_exception(self):
        expected_message = (
            "Cannot resolve keyword 'notafield' into field. Choices are: %s"
        )
        reporter_fields = ", ".join(sorted(f.name for f in Reporter._meta.get_fields()))
        with self.assertRaisesMessage(FieldError, expected_message % reporter_fields):
            Article.objects.values_list("reporter__notafield")
        article_fields = ", ".join(
            ["EXTRA"] + sorted(f.name for f in Article._meta.get_fields())
        )
        with self.assertRaisesMessage(FieldError, expected_message % article_fields):
            Article.objects.extra(select={"EXTRA": "EXTRA_SELECT"}).values_list(
                "notafield"
            )