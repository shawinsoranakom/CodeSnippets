def test_decorated_filter(self):
        engine = Engine(libraries=LIBRARIES)
        t = engine.from_string("{% load custom %}{{ name|make_data_div }}")
        self.assertEqual(
            t.render(Context({"name": "foo"})), '<div data-name="foo"></div>'
        )