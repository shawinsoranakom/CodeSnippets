def test_rename_m2m_field_with_2_references(self):
        app_label = "test_rename_many_refs"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    name="Person",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("name", models.CharField(max_length=255)),
                    ],
                ),
                migrations.CreateModel(
                    name="Relation",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "child",
                            models.ForeignKey(
                                on_delete=models.CASCADE,
                                related_name="relations_as_child",
                                to=f"{app_label}.person",
                            ),
                        ),
                        (
                            "parent",
                            models.ForeignKey(
                                on_delete=models.CASCADE,
                                related_name="relations_as_parent",
                                to=f"{app_label}.person",
                            ),
                        ),
                    ],
                ),
                migrations.AddField(
                    model_name="person",
                    name="parents_or_children",
                    field=models.ManyToManyField(
                        blank=True,
                        through=f"{app_label}.Relation",
                        to=f"{app_label}.person",
                    ),
                ),
            ],
        )
        Person = project_state.apps.get_model(app_label, "Person")
        Relation = project_state.apps.get_model(app_label, "Relation")

        person1 = Person.objects.create(name="John Doe")
        person2 = Person.objects.create(name="Jane Smith")
        Relation.objects.create(child=person2, parent=person1)

        self.assertTableExists(app_label + "_person")
        self.assertTableNotExists(app_label + "_other")

        self.apply_operations(
            app_label,
            project_state,
            operations=[
                migrations.RenameModel(old_name="Person", new_name="Other"),
            ],
        )

        self.assertTableNotExists(app_label + "_person")
        self.assertTableExists(app_label + "_other")