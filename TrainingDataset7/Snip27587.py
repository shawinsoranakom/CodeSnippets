def test_modelstate_get_field_order_wrt(self):
        new_apps = Apps()

        class Author(models.Model):
            name = models.TextField()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class Book(models.Model):
            author = models.ForeignKey(Author, models.CASCADE)

            class Meta:
                app_label = "migrations"
                apps = new_apps
                order_with_respect_to = "author"

        model_state = ModelState.from_model(Book)
        order_wrt_field = model_state.get_field("_order")
        self.assertIsInstance(order_wrt_field, models.ForeignKey)
        self.assertEqual(order_wrt_field.related_model, "migrations.author")