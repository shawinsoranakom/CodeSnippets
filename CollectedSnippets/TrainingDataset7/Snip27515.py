def test_create_model_add_field(self):
        """
        AddField should optimize into CreateModel.
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
                migrations.AddField("Foo", "age", models.IntegerField()),
            ],
            [
                migrations.CreateModel(
                    name="Foo",
                    fields=[
                        ("name", models.CharField(max_length=255)),
                        ("age", models.IntegerField()),
                    ],
                    options={"verbose_name": "Foo"},
                    bases=(UnicodeModel,),
                    managers=managers,
                ),
            ],
        )