def test_create_model_rename_field(self):
        """
        RenameField should optimize into CreateModel.
        """
        managers = [("objects", EmptyManager())]
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    name="Foo",
                    fields=[("name", models.CharField(max_length=255))],
                    options={"verbose_name": "Foo"},
                    bases=(UnicodeModel,),
                    managers=managers,
                ),
                migrations.RenameField("Foo", "name", "title"),
            ],
            [
                migrations.CreateModel(
                    name="Foo",
                    fields=[
                        ("title", models.CharField(max_length=255)),
                    ],
                    options={"verbose_name": "Foo"},
                    bases=(UnicodeModel,),
                    managers=managers,
                ),
            ],
        )