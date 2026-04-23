def test_include_recursive(self):
        comments = [
            {
                "comment": "A1",
                "children": [
                    {"comment": "B1", "children": []},
                    {"comment": "B2", "children": []},
                    {"comment": "B3", "children": [{"comment": "C1", "children": []}]},
                ],
            }
        ]
        with self.subTest(template="recursive_include.html"):
            engine = Engine(app_dirs=True)
            t = engine.get_template("recursive_include.html")
            self.assertEqual(
                "Recursion!  A1  Recursion!  B1   B2   B3  Recursion!  C1",
                t.render(Context({"comments": comments}))
                .replace(" ", "")
                .replace("\n", " ")
                .strip(),
            )
        with self.subTest(template="recursive_relative_include.html"):
            engine = Engine(app_dirs=True)
            t = engine.get_template("recursive_relative_include.html")
            self.assertEqual(
                "Recursion!  A1  Recursion!  B1   B2   B3  Recursion!  C1",
                t.render(Context({"comments": comments}))
                .replace(" ", "")
                .replace("\n", " ")
                .strip(),
            )
        with self.subTest(template="tmpl"):
            engine = Engine()
            template = """
            Recursion!
            {% for c in comments %}
              {{ c.comment }}
              {% if c.children %}{% include tmpl with comments=c.children %}{% endif %}
            {% endfor %}
            """
            outer_tmpl = engine.from_string("{% include tmpl %}")
            output = outer_tmpl.render(
                Context({"tmpl": engine.from_string(template), "comments": comments})
            )
            self.assertEqual(
                "Recursion!  A1  Recursion!  B1   B2   B3  Recursion!  C1",
                output.replace(" ", "").replace("\n", " ").strip(),
            )