def test_missing_model(self):
        """
        Displaying content types in admin (or anywhere) doesn't break on
        leftover content type records in the DB for which no model is defined
        anymore.
        """
        ct = ContentType.objects.create(
            app_label="contenttypes",
            model="OldModel",
        )
        self.assertEqual(str(ct), "contenttypes | OldModel")
        self.assertIsNone(ct.model_class())

        # Stale ContentTypes can be fetched like any other object.
        ct_fetched = ContentType.objects.get_for_id(ct.pk)
        self.assertIsNone(ct_fetched.model_class())