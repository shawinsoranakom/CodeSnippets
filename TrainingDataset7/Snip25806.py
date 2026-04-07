def test_values_nonexistent_field(self):
        # However, an exception FieldDoesNotExist will be thrown if you specify
        # a nonexistent field name in values() (a field that is neither in the
        # model nor in extra(select)).
        msg = (
            "Cannot resolve keyword 'id_plus_two' into field. Choices are: "
            "author, author_id, headline, id, id_plus_one, pub_date, slug, tag"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.extra(select={"id_plus_one": "id + 1"}).values(
                "id", "id_plus_two"
            )