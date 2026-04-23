def test_dates_fails_when_given_invalid_field_argument(self):
        with self.assertRaisesMessage(
            FieldError,
            "Cannot resolve keyword 'invalid_field' into field. Choices are: "
            "categories, comments, id, pub_date, pub_datetime, title",
        ):
            Article.objects.dates("invalid_field", "year")