def test_invalid_order_by(self):
        msg = "Cannot resolve keyword '*' into field. Choices are: created, id, name"
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.order_by("*")