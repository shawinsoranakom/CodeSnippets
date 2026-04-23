def test_choices_named_group(self):
        class Model(models.Model):
            field = models.UUIDField(
                choices=[
                    [
                        "knights",
                        [
                            [
                                uuid.UUID("5c859437-d061-4847-b3f7-e6b78852f8c8"),
                                "Lancelot",
                            ],
                            [
                                uuid.UUID("c7853ec1-2ea3-4359-b02d-b54e8f1bcee2"),
                                "Galahad",
                            ],
                        ],
                    ],
                    [uuid.UUID("25d405be-4895-4d50-9b2e-d6695359ce47"), "Other"],
                ],
            )

        self.assertEqual(Model._meta.get_field("field").check(), [])