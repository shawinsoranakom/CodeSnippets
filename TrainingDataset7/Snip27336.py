def test_add_textfield(self):
        """
        Tests the AddField operation on TextField.
        """
        project_state = self.set_up_test_model("test_adtxtfl")

        Pony = project_state.apps.get_model("test_adtxtfl", "Pony")
        pony = Pony.objects.create(weight=42)

        new_state = self.apply_operations(
            "test_adtxtfl",
            project_state,
            [
                migrations.AddField(
                    "Pony",
                    "text",
                    models.TextField(default="some text"),
                ),
                migrations.AddField(
                    "Pony",
                    "empty",
                    models.TextField(default=""),
                ),
                # If not properly quoted digits would be interpreted as an int.
                migrations.AddField(
                    "Pony",
                    "digits",
                    models.TextField(default="42"),
                ),
                # Manual quoting is fragile and could trip on quotes.
                migrations.AddField(
                    "Pony",
                    "quotes",
                    models.TextField(default='"\'"'),
                ),
            ],
        )

        Pony = new_state.apps.get_model("test_adtxtfl", "Pony")
        pony = Pony.objects.get(pk=pony.pk)
        self.assertEqual(pony.text, "some text")
        self.assertEqual(pony.empty, "")
        self.assertEqual(pony.digits, "42")
        self.assertEqual(pony.quotes, '"\'"')