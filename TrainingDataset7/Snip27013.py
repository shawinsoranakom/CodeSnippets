def set_up_test_model(
        self,
        app_label,
        second_model=False,
        third_model=False,
        index=False,
        multicol_index=False,
        related_model=False,
        mti_model=False,
        proxy_model=False,
        manager_model=False,
        unique_together=False,
        options=False,
        db_table=None,
        constraints=None,
        indexes=None,
    ):
        """Creates a test model state and database table."""
        # Make the "current" state.
        model_options = {"swappable": "TEST_SWAP_MODEL"}
        if options:
            model_options["permissions"] = [("can_groom", "Can groom")]
        if db_table:
            model_options["db_table"] = db_table
        if unique_together:
            model_options["unique_together"] = {("pink", "weight")}
        operations = [
            migrations.CreateModel(
                "Pony",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("pink", models.IntegerField(default=3)),
                    ("weight", models.FloatField()),
                    ("green", models.IntegerField(null=True)),
                    (
                        "yellow",
                        models.CharField(
                            blank=True, null=True, db_default="Yellow", max_length=20
                        ),
                    ),
                ],
                options=model_options,
            )
        ]
        if index:
            operations.append(
                migrations.AddIndex(
                    "Pony",
                    models.Index(fields=["pink"], name="pony_pink_idx"),
                )
            )
        if multicol_index:
            operations.append(
                migrations.AddIndex(
                    "Pony",
                    models.Index(fields=["pink", "weight"], name="pony_test_idx"),
                )
            )
        if indexes:
            for index in indexes:
                operations.append(migrations.AddIndex("Pony", index))
        if constraints:
            for constraint in constraints:
                operations.append(migrations.AddConstraint("Pony", constraint))
        if second_model:
            operations.append(
                migrations.CreateModel(
                    "Stable",
                    [
                        ("id", models.AutoField(primary_key=True)),
                    ],
                )
            )
        if third_model:
            operations.append(
                migrations.CreateModel(
                    "Van",
                    [
                        ("id", models.AutoField(primary_key=True)),
                    ],
                )
            )
        if related_model:
            operations.append(
                migrations.CreateModel(
                    "Rider",
                    [
                        ("id", models.AutoField(primary_key=True)),
                        ("pony", models.ForeignKey("Pony", models.CASCADE)),
                        (
                            "friend",
                            models.ForeignKey("self", models.CASCADE, null=True),
                        ),
                    ],
                )
            )
        if mti_model:
            operations.append(
                migrations.CreateModel(
                    "ShetlandPony",
                    fields=[
                        (
                            "pony_ptr",
                            models.OneToOneField(
                                "Pony",
                                models.CASCADE,
                                auto_created=True,
                                parent_link=True,
                                primary_key=True,
                                to_field="id",
                                serialize=False,
                            ),
                        ),
                        ("cuteness", models.IntegerField(default=1)),
                    ],
                    bases=["%s.Pony" % app_label],
                )
            )
        if proxy_model:
            operations.append(
                migrations.CreateModel(
                    "ProxyPony",
                    fields=[],
                    options={"proxy": True},
                    bases=["%s.Pony" % app_label],
                )
            )
        if manager_model:
            from .models import FoodManager, FoodQuerySet

            operations.append(
                migrations.CreateModel(
                    "Food",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                    ],
                    managers=[
                        ("food_qs", FoodQuerySet.as_manager()),
                        ("food_mgr", FoodManager("a", "b")),
                        ("food_mgr_kwargs", FoodManager("x", "y", 3, 4)),
                    ],
                )
            )
        return self.apply_operations(app_label, ProjectState(), operations)