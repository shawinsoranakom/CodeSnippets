def test_create_model_with_duplicate_base(self):
        message = "Found duplicate value test_crmo.pony in CreateModel bases argument."
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    "test_crmo.Pony",
                    "test_crmo.Pony",
                ),
            )
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    "test_crmo.Pony",
                    "test_crmo.pony",
                ),
            )
        message = (
            "Found duplicate value migrations.unicodemodel in CreateModel bases "
            "argument."
        )
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    UnicodeModel,
                    UnicodeModel,
                ),
            )
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    UnicodeModel,
                    "migrations.unicodemodel",
                ),
            )
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    UnicodeModel,
                    "migrations.UnicodeModel",
                ),
            )
        message = (
            "Found duplicate value <class 'django.db.models.base.Model'> in "
            "CreateModel bases argument."
        )
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    models.Model,
                    models.Model,
                ),
            )
        message = (
            "Found duplicate value <class 'migrations.test_operations.Mixin'> in "
            "CreateModel bases argument."
        )
        with self.assertRaisesMessage(ValueError, message):
            migrations.CreateModel(
                "Pony",
                fields=[],
                bases=(
                    Mixin,
                    Mixin,
                ),
            )