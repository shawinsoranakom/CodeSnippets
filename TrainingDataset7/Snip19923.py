def test_get_for_model_create_contenttype(self):
        """
        ContentTypeManager.get_for_model() creates the corresponding content
        type if it doesn't exist in the database.
        """

        class ModelCreatedOnTheFly(models.Model):
            name = models.CharField()

        ct = ContentType.objects.get_for_model(ModelCreatedOnTheFly)
        self.assertEqual(ct.app_label, "contenttypes_tests")
        self.assertEqual(ct.model, "modelcreatedonthefly")
        self.assertEqual(str(ct), "contenttypes_tests | modelcreatedonthefly")