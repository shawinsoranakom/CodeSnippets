def test_repr(self):
        a = self.engine.get_template("index.html")
        name = os.path.join(TEMPLATE_DIR, "index.html")
        self.assertEqual(repr(a.origin), "<Origin name=%r>" % name)