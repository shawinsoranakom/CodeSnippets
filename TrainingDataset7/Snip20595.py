def test_concat_non_str(self):
        Author.objects.create(name="The Name", age=42)
        with self.assertNumQueries(1) as ctx:
            author = Author.objects.annotate(
                name_text=Concat(
                    "name", V(":"), "alias", V(":"), "age", output_field=TextField()
                ),
            ).get()
        self.assertEqual(author.name_text, "The Name::42")
        # Only non-string columns are casted on PostgreSQL.
        self.assertEqual(
            ctx.captured_queries[0]["sql"].count("::text"),
            1 if connection.vendor == "postgresql" else 0,
        )