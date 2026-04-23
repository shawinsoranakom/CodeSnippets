def test_clash_between_related_query_name_and_manager(self):
        class Author(models.Model):
            authors = models.Manager()
            mentor = models.ForeignKey(
                "self", related_name="authors", on_delete=models.CASCADE
            )

        self.assertEqual(
            Author.check(),
            [
                Error(
                    "Related name 'authors' for 'invalid_models_tests.Author.mentor' "
                    "clashes with the name of a model manager.",
                    hint=(
                        "Rename the model manager or change the related_name argument "
                        "in the definition for field "
                        "'invalid_models_tests.Author.mentor'."
                    ),
                    obj=Author._meta.get_field("mentor"),
                    id="fields.E348",
                )
            ],
        )