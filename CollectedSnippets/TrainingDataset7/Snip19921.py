def test_get_for_models_migrations_create_model(self):
        state = ProjectState.from_apps(apps.get_app_config("contenttypes"))

        class Foo(models.Model):
            class Meta:
                app_label = "contenttypes_tests"

        state.add_model(ModelState.from_model(Foo))
        ContentType = state.apps.get_model("contenttypes", "ContentType")
        cts = ContentType.objects.get_for_models(FooWithUrl, Foo)
        self.assertEqual(
            cts,
            {
                Foo: ContentType.objects.get_for_model(Foo),
                FooWithUrl: ContentType.objects.get_for_model(FooWithUrl),
            },
        )