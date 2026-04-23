def test_missing_model_with_existing_model_name(self):
        """
        Displaying content types in admin (or anywhere) doesn't break on
        leftover content type records in the DB for which no model is defined
        anymore, even if a model with the same name exists in another app.
        """
        # Create a stale ContentType that matches the name of an existing
        # model.
        ContentType.objects.create(app_label="contenttypes", model="author")
        ContentType.objects.clear_cache()
        # get_for_models() should work as expected for existing models.
        cts = ContentType.objects.get_for_models(ContentType, Author)
        self.assertEqual(
            cts,
            {
                ContentType: ContentType.objects.get_for_model(ContentType),
                Author: ContentType.objects.get_for_model(Author),
            },
        )