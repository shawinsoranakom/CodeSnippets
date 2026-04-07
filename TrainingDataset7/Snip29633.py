def test_choices_tuple_list(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(
                models.CharField(max_length=16),
                choices=[
                    [
                        "Media",
                        [(["vinyl", "cd"], "Audio"), (("vhs", "dvd"), "Video")],
                    ],
                    (["mp3", "mp4"], "Digital"),
                ],
            )

        self.assertEqual(MyModel._meta.get_field("field").check(), [])