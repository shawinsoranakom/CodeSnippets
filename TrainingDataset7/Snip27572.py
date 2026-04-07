def test_render_model_inheritance(self):
        class Book(models.Model):
            title = models.CharField(max_length=1000)

            class Meta:
                app_label = "migrations"
                apps = Apps()

        class Novel(Book):
            class Meta:
                app_label = "migrations"
                apps = Apps()

        # First, test rendering individually
        apps = Apps(["migrations"])

        # We shouldn't be able to render yet
        ms = ModelState.from_model(Novel)
        with self.assertRaises(InvalidBasesError):
            ms.render(apps)

        # Once the parent model is in the app registry, it should be fine
        ModelState.from_model(Book).render(apps)
        ModelState.from_model(Novel).render(apps)