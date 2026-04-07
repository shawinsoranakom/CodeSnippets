def test_autoescape_off(self):
        engine = Engine(dirs=[TEMPLATE_DIR], autoescape=False)
        self.assertEqual(
            engine.render_to_string("test_context.html", {"obj": "<script>"}),
            "obj:<script>\n",
        )