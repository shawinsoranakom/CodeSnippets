def test_render_context_is_cleared(self):
        """
        #24555 -- InclusionNode should push and pop the render_context stack
        when rendering. Otherwise, leftover values such as blocks from
        extending can interfere with subsequent rendering.
        """
        engine = Engine(app_dirs=True, libraries=LIBRARIES)
        template = engine.from_string(
            "{% load inclusion %}{% inclusion_extends1 %}{% inclusion_extends2 %}"
        )
        self.assertEqual(template.render(Context({})).strip(), "one\ntwo")