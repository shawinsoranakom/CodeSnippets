def test_unavailable_content_type_model(self):
        """A ContentType isn't created if the model isn't available."""
        apps = Apps()
        with self.assertNumQueries(0):
            contenttypes_management.create_contenttypes(
                self.app_config, interactive=False, verbosity=0, apps=apps
            )
        self.assertEqual(ContentType.objects.count(), self.before_count + 1)