def test_get_field_display_nested_array(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(
                ArrayField(models.CharField(max_length=16)),
                choices=[
                    [
                        "Media",
                        [([["vinyl", "cd"], ("x",)], "Audio")],
                    ],
                    ((["mp3"], ("mp4",)), "Digital"),
                ],
            )

        tests = (
            ([["vinyl", "cd"], ("x",)], "Audio"),
            ((["mp3"], ("mp4",)), "Digital"),
            ((("a", "b"), ("c",)), "(('a', 'b'), ('c',))"),
            ([["a", "b"], ["c"]], "[['a', 'b'], ['c']]"),
        )
        for value, display in tests:
            with self.subTest(value=value, display=display):
                instance = MyModel(field=value)
                self.assertEqual(instance.get_field_display(), display)