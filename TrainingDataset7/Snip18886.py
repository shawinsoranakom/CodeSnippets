def test_can_initialize_model_instance_using_positional_arguments(self):
        """
        You can initialize a model instance using positional arguments,
        which should match the field order as defined in the model.
        """
        a = Article(None, "Second article", datetime(2005, 7, 29))
        a.save()

        self.assertEqual(a.headline, "Second article")
        self.assertEqual(a.pub_date, datetime(2005, 7, 29, 0, 0))