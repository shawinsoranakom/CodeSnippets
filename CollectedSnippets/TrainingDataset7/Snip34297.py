def test_extend_cached(self):
        engine = Engine(
            dirs=[
                os.path.join(RECURSIVE, "fs"),
                os.path.join(RECURSIVE, "fs2"),
                os.path.join(RECURSIVE, "fs3"),
            ],
            loaders=[
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                    ],
                ),
            ],
        )
        template = engine.get_template("recursive.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "fs3/recursive fs2/recursive fs/recursive")

        cache = engine.template_loaders[0].get_template_cache
        self.assertEqual(len(cache), 3)
        expected_path = os.path.join("fs", "recursive.html")
        self.assertTrue(cache["recursive.html"].origin.name.endswith(expected_path))

        # Render another path that uses the same templates from the cache
        template = engine.get_template("other-recursive.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "fs3/recursive fs2/recursive fs/recursive")

        # Template objects should not be duplicated.
        self.assertEqual(len(cache), 4)
        expected_path = os.path.join("fs", "other-recursive.html")
        self.assertTrue(
            cache["other-recursive.html"].origin.name.endswith(expected_path)
        )