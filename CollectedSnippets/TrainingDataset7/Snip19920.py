def test_get_for_models_migrations(self):
        state = ProjectState.from_apps(apps.get_app_config("contenttypes"))
        ContentType = state.apps.get_model("contenttypes", "ContentType")
        cts = ContentType.objects.get_for_models(ContentType)
        self.assertEqual(
            cts, {ContentType: ContentType.objects.get_for_model(ContentType)}
        )