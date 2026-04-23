def test_extend_recursive(self):
        engine = Engine(
            dirs=[
                os.path.join(RECURSIVE, "fs"),
                os.path.join(RECURSIVE, "fs2"),
                os.path.join(RECURSIVE, "fs3"),
            ]
        )
        template = engine.get_template("recursive.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "fs3/recursive fs2/recursive fs/recursive")