def test_add_charfield(self):
        """
        Tests the AddField operation on TextField.
        """
        project_state = self.set_up_test_model("test_adchfl")

        Pony = project_state.apps.get_model("test_adchfl", "Pony")
        pony = Pony.objects.create(weight=42)

        new_state = self.apply_operations(
            "test_adchfl",
            project_state,
            [
                migrations.AddField(
                    "Pony",
                    "text",
                    models.CharField(max_length=10, default="some text"),
                ),
                migrations.AddField(
                    "Pony",
                    "empty",
                    models.CharField(max_length=10, default=""),
                ),
                # If not properly quoted digits would be interpreted as an int.
                migrations.AddField(
                    "Pony",
                    "digits",
                    models.CharField(max_length=10, default="42"),
                ),
                # Manual quoting is fragile and could trip on quotes.
                migrations.AddField(
                    "Pony",
                    "quotes",
                    models.CharField(max_length=10, default='"\'"'),
                ),
            ],
        )

        Pony = new_state.apps.get_model("test_adchfl", "Pony")
        pony = Pony.objects.get(pk=pony.pk)
        self.assertEqual(pony.text, "some text")
        self.assertEqual(pony.empty, "")
        self.assertEqual(pony.digits, "42")
        self.assertEqual(pony.quotes, '"\'"')