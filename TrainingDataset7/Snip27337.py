def test_add_binaryfield(self):
        """
        Tests the AddField operation on TextField/BinaryField.
        """
        project_state = self.set_up_test_model("test_adbinfl")

        Pony = project_state.apps.get_model("test_adbinfl", "Pony")
        pony = Pony.objects.create(weight=42)

        new_state = self.apply_operations(
            "test_adbinfl",
            project_state,
            [
                migrations.AddField(
                    "Pony",
                    "blob",
                    models.BinaryField(default=b"some text"),
                ),
                migrations.AddField(
                    "Pony",
                    "empty",
                    models.BinaryField(default=b""),
                ),
                # If not properly quoted digits would be interpreted as an int.
                migrations.AddField(
                    "Pony",
                    "digits",
                    models.BinaryField(default=b"42"),
                ),
                # Manual quoting is fragile and could trip on quotes.
                migrations.AddField(
                    "Pony",
                    "quotes",
                    models.BinaryField(default=b'"\'"'),
                ),
            ],
        )

        Pony = new_state.apps.get_model("test_adbinfl", "Pony")
        pony = Pony.objects.get(pk=pony.pk)
        # SQLite returns buffer/memoryview, cast to bytes for checking.
        self.assertEqual(bytes(pony.blob), b"some text")
        self.assertEqual(bytes(pony.empty), b"")
        self.assertEqual(bytes(pony.digits), b"42")
        self.assertEqual(bytes(pony.quotes), b'"\'"')